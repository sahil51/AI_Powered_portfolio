from application.ai.interfaces import AIProvider
from application.ai.manager import ProviderManager
from application.ai.registry import ProviderRegistry
from application.context import app_context
from application.di.container import container
from application.di.lifecycle import StartupHook, lifecycle
from application.di.providers import (
    ConfigProvider,
    DatabaseProvider,
    LLMProvider,
    RedisProvider,
    TaskQueueProvider,
)
from application.exceptions import BootstrapError
from application.knowledge_context.assembler import KnowledgeContextAssemblerImpl
from application.knowledge_context.builder import KnowledgeContextBuilder
from application.knowledge_context.cache import KnowledgeContextCache
from application.knowledge_context.compressor import KnowledgeContextCompressor
from application.knowledge_context.health import KnowledgeContextHealthChecker
from application.knowledge_context.metrics import KnowledgeContextMetricsCollector
from application.knowledge_context.policy import KnowledgeContextPolicy
from application.knowledge_context.provider import KnowledgeRetrievalProvider
from application.knowledge_context.statistics import KnowledgeContextStatisticsCollector
from application.knowledge_context.validator import KnowledgeContextValidator
from application.knowledge_ingestion.deduplicator import KnowledgeDeduplicator
from application.knowledge_ingestion.importer import KnowledgeImporter
from application.knowledge_ingestion.normalizer import KnowledgeNormalizer
from application.knowledge_ingestion.processor import KnowledgeProcessor
from application.knowledge_ingestion.scheduler import KnowledgeScheduler
from application.knowledge_ingestion.service import KnowledgeIngestionService
from application.knowledge_ingestion.validators import KnowledgeImportValidator
from application.knowledge_ingestion.version_manager import KnowledgeVersionManager
from application.prompts.registry import PromptRegistry
from application.retrieval.hybrid_service import HybridRetrievalService
from application.retrieval.search_service import KnowledgeSearchService
from domain.knowledge.factory import KnowledgeFactory
from domain.knowledge.lifecycle import KnowledgeLifecycle
from domain.knowledge.repository import KnowledgeRepository
from infrastructure.cache.redis_client import CacheService
from infrastructure.database.session import db
from infrastructure.llm.lite_llm_config import LiteLLMConfiguration
from infrastructure.llm.lite_llm_provider import LiteLLMProvider
from infrastructure.persistence.repository import SQLAlchemyKnowledgeRepository
from monitoring.logger import logger


class ApplicationBootstrap:
    def __init__(self) -> None:
        self._providers: list = []
        self._bootstrapped = False

    async def bootstrap(self) -> None:
        if self._bootstrapped:
            return

        logger.info("Bootstrapping application")

        config_provider = ConfigProvider()
        db_provider = DatabaseProvider()
        redis_provider = RedisProvider()
        llm_provider = LLMProvider()
        task_queue_provider = TaskQueueProvider()

        self._providers = [
            config_provider,
            db_provider,
            redis_provider,
            llm_provider,
            task_queue_provider,
        ]

        container.register_instance(ConfigProvider, config_provider)
        container.register_instance(DatabaseProvider, db_provider)
        container.register_instance(RedisProvider, redis_provider)
        container.register_instance(LLMProvider, llm_provider)
        container.register_instance(TaskQueueProvider, task_queue_provider)

        for provider in self._providers:
            try:
                await provider.bootstrap()
            except Exception as e:
                raise BootstrapError(
                    message=f"Provider {provider.__class__.__name__} bootstrap failed",
                    detail=str(e),
                )

        litellm_config = LiteLLMConfiguration.from_settings()
        litellm_provider = LiteLLMProvider(config=litellm_config)
        await litellm_provider.initialize()
        container.register_instance(AIProvider, litellm_provider)

        provider_registry = ProviderRegistry()
        provider_registry.register(litellm_provider, make_default=True)
        container.register_instance(ProviderRegistry, provider_registry)

        provider_manager = ProviderManager(provider_registry)
        container.register_instance(ProviderManager, provider_manager)

        knowledge_factory = KnowledgeFactory()
        knowledge_lifecycle = KnowledgeLifecycle()
        knowledge_repository = SQLAlchemyKnowledgeRepository(db.session_factory())
        knowledge_validator = KnowledgeImportValidator()
        knowledge_normalizer = KnowledgeNormalizer()
        knowledge_deduplicator = KnowledgeDeduplicator()
        knowledge_version_manager = KnowledgeVersionManager()

        container.register_instance(KnowledgeFactory, knowledge_factory)
        container.register_instance(KnowledgeLifecycle, knowledge_lifecycle)
        container.register_instance(KnowledgeRepository, knowledge_repository)
        container.register_instance(SQLAlchemyKnowledgeRepository, knowledge_repository)
        container.register_instance(KnowledgeImportValidator, knowledge_validator)
        container.register_instance(KnowledgeNormalizer, knowledge_normalizer)
        container.register_instance(KnowledgeDeduplicator, knowledge_deduplicator)
        container.register_instance(KnowledgeVersionManager, knowledge_version_manager)

        knowledge_processor = KnowledgeProcessor(
            repository=knowledge_repository,
            embedding_pipeline=None,
            normalizer=knowledge_normalizer,
            deduplicator=knowledge_deduplicator,
            version_manager=knowledge_version_manager,
            validator=knowledge_validator,
            lifecycle=knowledge_lifecycle,
            factory=knowledge_factory,
        )
        container.register_instance(KnowledgeProcessor, knowledge_processor)

        knowledge_importer = KnowledgeImporter(
            processor=knowledge_processor,
            repository=knowledge_repository,
            validator=knowledge_validator,
        )
        container.register_instance(KnowledgeImporter, knowledge_importer)

        knowledge_ingestion_service = KnowledgeIngestionService(
            importer=knowledge_importer,
            validator=knowledge_validator,
        )
        container.register_instance(
            KnowledgeIngestionService, knowledge_ingestion_service
        )

        knowledge_scheduler = KnowledgeScheduler(knowledge_ingestion_service)
        container.register_instance(KnowledgeScheduler, knowledge_scheduler)

        # Knowledge Context service registrations
        cache_service = CacheService(redis=redis_provider.client)
        container.register_instance(CacheService, cache_service)

        context_compressor = KnowledgeContextCompressor()
        container.register_instance(KnowledgeContextCompressor, context_compressor)

        context_assembler = KnowledgeContextAssemblerImpl(compressor=context_compressor)
        container.register_instance(KnowledgeContextAssemblerImpl, context_assembler)

        context_cache = KnowledgeContextCache(cache_service=cache_service)
        container.register_instance(KnowledgeContextCache, context_cache)

        context_policy = KnowledgeContextPolicy()
        container.register_instance(KnowledgeContextPolicy, context_policy)

        context_validator = KnowledgeContextValidator()
        container.register_instance(KnowledgeContextValidator, context_validator)

        context_health_checker = KnowledgeContextHealthChecker()
        container.register_instance(KnowledgeContextHealthChecker, context_health_checker)

        context_metrics_collector = KnowledgeContextMetricsCollector()
        container.register_instance(KnowledgeContextMetricsCollector, context_metrics_collector)

        context_statistics_collector = KnowledgeContextStatisticsCollector()
        container.register_instance(KnowledgeContextStatisticsCollector, context_statistics_collector)

        container.register(HybridRetrievalService, HybridRetrievalService)
        container.register(KnowledgeSearchService, KnowledgeSearchService)

        prompt_registry = PromptRegistry()
        await prompt_registry.load_registry()
        container.register_instance(PromptRegistry, prompt_registry)

        context_retrieval_provider = KnowledgeRetrievalProvider(
            search_service=container.resolve(KnowledgeSearchService),
        )
        container.register_instance(KnowledgeRetrievalProvider, context_retrieval_provider)

        context_builder = KnowledgeContextBuilder(
            provider=context_retrieval_provider,
            assembler=context_assembler,
            cache=context_cache,
            policy=context_policy,
            validator=context_validator,
            metrics_collector=context_metrics_collector,
            statistics_collector=context_statistics_collector,
            health_checker=context_health_checker,
        )
        container.register_instance(KnowledgeContextBuilder, context_builder)

        from observability.manager import ObservabilityManager
        observability_manager = ObservabilityManager()
        await observability_manager.initialize()
        container.register_instance(ObservabilityManager, observability_manager)

        from security.manager import SecurityManager
        security_manager = SecurityManager()
        await security_manager.initialize()
        container.register_instance(SecurityManager, security_manager)

        from evaluation.manager import EvaluationManager
        evaluation_manager = EvaluationManager()
        await evaluation_manager.initialize()
        container.register_instance(EvaluationManager, evaluation_manager)

        from production.validator import ProductionValidator
        production_validator = ProductionValidator()
        await production_validator.initialize()
        container.register_instance(ProductionValidator, production_validator)

        # Performance & Scalability registrations
        from performance.benchmark import PerformanceBenchmark
        from performance.concurrency import ConcurrencyTester
        from performance.health import PerformanceHealth
        from performance.load_runner import LoadTestRunner
        from performance.manager import PerformanceManager
        from performance.metrics import PerformanceMetrics
        from performance.profiler import ConnectionPoolProfiler, PerformanceProfiler
        from performance.stress_runner import StressTestRunner
        from performance.validator import PerformanceValidator

        perf_profiler = PerformanceProfiler()
        conn_pool_profiler = ConnectionPoolProfiler()
        perf_metrics = PerformanceMetrics()
        perf_validator = PerformanceValidator()

        # Instantiate benchmark with resolved cache service as fallback for short-term memory
        perf_benchmark = PerformanceBenchmark(
            short_term_memory=container.resolve(CacheService) if container.has_registration(CacheService) else None
        )

        load_test_runner = LoadTestRunner()
        stress_test_runner = StressTestRunner()
        concurrency_tester = ConcurrencyTester()
        perf_health = PerformanceHealth(perf_profiler, conn_pool_profiler)
        perf_manager = PerformanceManager(
            profiler=perf_profiler,
            pool_profiler=conn_pool_profiler,
            benchmark=perf_benchmark,
            validator=perf_validator,
        )

        container.register_instance(PerformanceProfiler, perf_profiler)
        container.register_instance(ConnectionPoolProfiler, conn_pool_profiler)
        container.register_instance(PerformanceMetrics, perf_metrics)
        container.register_instance(PerformanceValidator, perf_validator)
        container.register_instance(PerformanceBenchmark, perf_benchmark)
        container.register_instance(LoadTestRunner, load_test_runner)
        container.register_instance(StressTestRunner, stress_test_runner)
        container.register_instance(ConcurrencyTester, concurrency_tester)
        container.register_instance(PerformanceHealth, perf_health)
        container.register_instance(PerformanceManager, perf_manager)

        lifecycle.add_startup_hook(
            StartupHook(
                name="db_init",
                handler=db_provider.bootstrap,
                priority=10,
                critical=True,
            )
        )
        lifecycle.add_startup_hook(
            StartupHook(
                name="redis_init",
                handler=redis_provider.bootstrap,
                priority=20,
                critical=False,
            )
        )
        lifecycle.add_startup_hook(
            StartupHook(
                name="llm_init",
                handler=llm_provider.bootstrap,
                priority=30,
                critical=False,
            )
        )
        lifecycle.add_startup_hook(
            StartupHook(
                name="task_queue_init",
                handler=task_queue_provider.bootstrap,
                priority=40,
                critical=False,
            )
        )

        await lifecycle.run_startup()
        app_context.started = True
        self._bootstrapped = True
        logger.info("Application bootstrapped successfully")

    async def shutdown(self) -> None:
        if not self._bootstrapped:
            return

        logger.info("Shutting down application")
        await lifecycle.run_shutdown()

        from observability.manager import ObservabilityManager
        obs_mgr = container.resolve(ObservabilityManager)
        await obs_mgr.shutdown()

        from security.manager import SecurityManager
        sec_mgr = container.resolve(SecurityManager)
        await sec_mgr.shutdown()

        from evaluation.manager import EvaluationManager
        eval_mgr = container.resolve(EvaluationManager)
        await eval_mgr.shutdown()

        from production.validator import ProductionValidator
        prod_validator = container.resolve(ProductionValidator)
        await prod_validator.shutdown()

        for provider in reversed(self._providers):
            try:
                await provider.shutdown()
            except Exception as e:
                logger.warning(f"Provider {provider.__class__.__name__} shutdown error: {e}")

        container.clear()
        app_context.clear()
        self._bootstrapped = False
        app_context.started = False
        logger.info("Application shut down")

    @property
    def bootstrapped(self) -> bool:
        return self._bootstrapped


bootstrap_manager = ApplicationBootstrap()
