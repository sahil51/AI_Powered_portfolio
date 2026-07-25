document.addEventListener("DOMContentLoaded", function () {
    function initCKEditor(selector) {
        const element = document.querySelector(selector);
        if (element && !element.dataset.ckeditorInitialized) {
            element.dataset.ckeditorInitialized = "true";

            const EditorFactory = (window.CKEDITOR && window.CKEDITOR.ClassicEditor) 
                ? window.CKEDITOR.ClassicEditor 
                : (typeof ClassicEditor !== 'undefined' ? ClassicEditor : null);

            if (!EditorFactory) {
                console.error("CKEditor script not loaded.");
                return;
            }

            EditorFactory.create(element, {
                toolbar: {
                    items: [
                        'heading', '|',
                        'bold', 'italic', 'underline', 'strikethrough', 'fontColor', 'fontBackgroundColor', '|',
                        'link', 'insertImage', 'mediaEmbed', 'codeBlock', '|',
                        'bulletedList', 'numberedList', 'blockQuote', '|',
                        'insertTable', 'sourceEditing', '|',
                        'undo', 'redo'
                    ],
                    shouldNotGroupWhenFull: true
                },
                image: {
                    toolbar: [
                        'imageTextAlternative', 'toggleImageCaption', 'imageStyle:inline', 'imageStyle:block', 'imageStyle:side', 'linkImage'
                    ]
                },
                table: {
                    contentToolbar: [
                        'tableColumn', 'tableRow', 'mergeTableCells', 'tableCellProperties', 'tableProperties'
                    ]
                },
                mediaEmbed: {
                    previewsInData: true
                },
                removePlugins: [
                    'ExportPdf', 'ExportWord', 'CKBox', 'CKFinder', 'EasyImage', 
                    'RealTimeCollaborativeComments', 'RealTimeCollaborativeTrackChanges',
                    'RealTimeCollaborativeRevisionHistory', 'PresenceList', 'Comments',
                    'TrackChanges', 'TrackChangesData', 'RevisionHistory', 'Pagination',
                    'WProofreader', 'MathType', 'SlashCommand', 'Template', 'DocumentOutline',
                    'FormatPainter', 'TableOfContents', 'PasteFromOfficeEnhanced'
                ]
            }).then(editor => {
                editor.model.document.on('change:data', () => {
                    element.value = editor.getData();
                });
            }).catch(error => {
                console.error("CKEditor initialization error on " + selector + ":", error);
            });
        }
    }

    initCKEditor('#id_summary');
    initCKEditor('#id_content');
});
