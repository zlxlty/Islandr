/*
 * @Author: Tianyi Lu
 * @Description: 
 * @Date: 2020-01-08 10:47:02
 * @LastEditors  : Tianyi Lu
 * @LastEditTime : 2020-01-08 11:04:38
 */
tinymce.init({ 
    //选择class为content的标签作为编辑器 
    selector: '#content', 
    //方向从左到右 
    directionality:'ltr', 
    //语言选择中文 language:'zh_CN', 
    //高度为400 
    height:400, 
    //工具栏上面的补丁按钮 
    plugins: [ 'advlist autolink link image imagetools lists charmap print preview hr anchor pagebreak spellchecker', 
    'searchreplace wordcount visualblocks visualchars code fullscreen insertdatetime nonbreaking', 
    'save table contextmenu directionality emoticons template paste textcolor'], 
    //工具栏的补丁按钮 
    imagetools_toolbar:"rotateleft rotateright | flipv fliph | editimage imageoptions",
    toolbar: 'insertfile undo redo |\
     styleselect |\
     bold italic |\
     alignleft aligncenter alignright alignjustify |\
     bullist numlist outdent indent |\
     link image |\
     print preview media fullpage |\
     forecolor backcolor emoticons |\
     codesample fontsizeselect fullscreen', 
    images_upload_url: "http://127.0.0.1:5000/imageuploader",
    automatic_uploads: true,
    images_reuse_filename: false,
    images_upload_base_path: '/static/uploads',
     //字体大小 
    fontsize_formats: '10pt 12pt 14pt 18pt 24pt 36pt', 
     //按tab不换行 
    nonbreaking_force_tab: true,
    templates: [
        {title: 'Some title 1', description: 'Some desc 1', content: 'My content'},
        // {title: 'Some title 2', description: 'Some desc 2', url: ''}
    ],
    init_instance_callback: "insert_contents",
});

