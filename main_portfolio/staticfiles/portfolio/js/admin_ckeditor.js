document.addEventListener("DOMContentLoaded", function () {
    var retryCount = 0;

    function initCKEditor(selector) {
        var element = document.querySelector(selector);
        if (!element || element.dataset.ckeditorInitialized) return;

        // Super-build exposes CKEDITOR.ClassicEditor
        var EditorClass = null;
        if (window.CKEDITOR && window.CKEDITOR.ClassicEditor) {
            EditorClass = window.CKEDITOR.ClassicEditor;
        }

        if (!EditorClass) {
            retryCount++;
            if (retryCount < 60) {
                setTimeout(function() { initCKEditor(selector); }, 300);
            } else {
                console.error("CKEditor SuperBuild not found after 60 retries for " + selector);
            }
            return;
        }

        element.dataset.ckeditorInitialized = "true";
        console.log("Initializing CKEditor SuperBuild on " + selector);

        EditorClass.create(element, {
            toolbar: {
                items: [
                    'heading', '|',
                    'bold', 'italic', 'underline', 'strikethrough', '|',
                    'link', 'uploadImage', 'mediaEmbed', '|',
                    'bulletedList', 'numberedList', 'blockQuote', '|',
                    'insertTable', '|',
                    'undo', 'redo'
                ],
                shouldNotGroupWhenFull: true
            },
            image: {
                resizeUnit: '%',
                resizeOptions: [
                    { name: 'resizeImage:original', value: null, label: 'Original size' },
                    { name: 'resizeImage:25', value: '25', label: '25%' },
                    { name: 'resizeImage:50', value: '50', label: '50%' },
                    { name: 'resizeImage:75', value: '75', label: '75%' }
                ],
                toolbar: [
                    'imageTextAlternative', 'toggleImageCaption', '|',
                    'imageStyle:inline', 'imageStyle:block', 'imageStyle:side', '|',
                    'imageStyle:alignLeft', 'imageStyle:alignCenter', 'imageStyle:alignRight', '|',
                    'resizeImage', '|',
                    'linkImage'
                ]
            },
            table: {
                contentToolbar: [
                    'tableColumn', 'tableRow', 'mergeTableCells'
                ]
            },
            removePlugins: [
                'ExportPdf',
                'ExportWord',
                'CKBox',
                'CKFinder',
                'EasyImage',
                'RealTimeCollaborativeComments',
                'RealTimeCollaborativeTrackChanges',
                'RealTimeCollaborativeRevisionHistory',
                'PresenceList',
                'Comments',
                'TrackChanges',
                'TrackChangesData',
                'RevisionHistory',
                'Pagination',
                'WProofreader',
                'MathType',
                'SlashCommand',
                'Template',
                'DocumentOutline',
                'FormatPainter',
                'TableOfContents',
                'PasteFromOfficeEnhanced',
                'CaseChange'
            ]
        }).then(function(editor) {
            console.log("CKEditor SuperBuild READY on " + selector);

            // Base64 image upload
            try {
                var fileRepo = editor.plugins.get('FileRepository');
                if (fileRepo) {
                    fileRepo.createUploadAdapter = function(loader) {
                        return {
                            upload: function() {
                                return loader.file.then(function(file) {
                                    return new Promise(function(resolve, reject) {
                                        var reader = new FileReader();
                                        reader.onload = function() { resolve({ "default": reader.result }); };
                                        reader.onerror = function(e) { reject(e); };
                                        reader.readAsDataURL(file);
                                    });
                                });
                            },
                            abort: function() {}
                        };
                    };
                }
            } catch(e) {}

            editor.model.document.on('change:data', function() {
                element.value = editor.getData();
            });
            if (element.form) {
                element.form.addEventListener('submit', function() {
                    element.value = editor.getData();
                });
            }
        }).catch(function(err) {
            console.error("CKEditor error on " + selector + ":", err);
            console.error("Error message:", err.message);
        });
    }

    // Delay to let CDN script fully load
    setTimeout(function() {
        initCKEditor('#id_summary');
        initCKEditor('#id_content');
    }, 1000);
});
