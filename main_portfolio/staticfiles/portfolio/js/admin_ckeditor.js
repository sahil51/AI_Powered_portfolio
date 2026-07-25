document.addEventListener("DOMContentLoaded", function () {
    function initCKEditor(selector) {
        const element = document.querySelector(selector);
        if (element && !element.dataset.ckeditorInitialized) {
            element.dataset.ckeditorInitialized = "true";
            ClassicEditor.create(element, {
                toolbar: [
                    'heading', '|',
                    'bold', 'italic', 'underline', 'strikethrough', 'link', '|',
                    'bulletedList', 'numberedList', 'blockQuote', '|',
                    'insertTable', 'undo', 'redo'
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
