var startTime;
var processing = false;
var timeout = 120;
function start() {
    startTime = new Date();
};
function elapsed() {
    endTime = new Date();
    var timeDiff = endTime - startTime;
    timeDiff /= 1000;
    return Math.round(timeDiff);
}
function render_content(content, filename) {
    if (typeof content.error !== 'undefined') {
        $("#report").text(content.error);
        mixpanel.track('Upload Failure', {
            'elapsed': elapsed(),
            'distinct_id': filename,
            'error': content.error
        });
    } else {
        $.ajax({
            type: 'POST',
            url: "/render",
            data: JSON.stringify(content),
            contentType: "application/json; charset=utf-8",
            success: function(data){
                $("#report").html(data);
                $("#upload-form").hide();
            }
        });
        mixpanel.track('Upload Success', {
            'elapsed': elapsed(),
            'distinct_id': filename,
            ...content.scores
        });
    }
}

var isAdvancedUpload = function() {
  var div = document.createElement('div');
  return (('draggable' in div) || ('ondragstart' in div && 'ondrop' in div)) && 'FormData' in window && 'FileReader' in window;
}();

var droppedFiles;

function updateData(file) {
    $('#filename').text(file.name);
    let extension = file.name.split('.').pop();
    $(".dropzone").removeClass("active");
    if (extension != 'docx' && extension != 'tex') {
        $(".file").addClass("is-danger");
        $(".file span.file-label").text("Must be .docx or .tex");
        $("form button[type=submit]").attr("disabled", "disabled");
    }
    else {
        $(".file").removeClass("is-danger");
        $(".file span.file-label").text("Choose a file…");
        $("form button[type=submit]").removeAttr("disabled");
        $(".dropzone").addClass("active");
    }
}

$(document).ready(function(){

    var $form = $('.dropzone');

    if (isAdvancedUpload) {

      $form.on('drag dragstart dragend dragover dragenter dragleave drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
      })
      .on('dragover dragenter', function() {
        $form.addClass('is-dragover');
      })
      .on('dragleave dragend drop', function() {
        $form.removeClass('is-dragover');
      })
      .on('drop', function(e) {
        droppedFiles = e.originalEvent.dataTransfer.files;
        if (droppedFiles.length > 0) {
            updateData(droppedFiles[0]);
        }
      });
    }

    $("#conference_id").val(Cookies.get('conference') ?? '');
    const file = document.getElementById("file");
    file.onchange = function(){
        if(file.files.length > 0) {
            updateData(file.files[0]);
            droppedFiles = false;
        }
    };
    setInterval(function(){
        if (processing) {
            $("#timer").text(elapsed() + " seconds elapsed, timeout set to " + timeout + " seconds");
        }
    },1000)

    var filesize = -1;
    var filename = 'Unknown';
    var conference = "Not Selected";


    $("form").submit(function(e){
        conference = $("#conference_id option:selected").text();
        Cookies.set('conference', $("#conference_id").val(), { expires: 31 });
        let field = document.getElementById('file');
        if (field.files[0] !== undefined) {
            filesize = field.files[0].size / 1000;
            filename = field.files[0].name;
        }
        processing = true;
        start();
        $(".progress").show();
        e.preventDefault();
        var formData = new FormData(this);

         if (droppedFiles) {
            formData.delete("document");
            $.each( droppedFiles, function(i, file) {
              formData.append( 'document', file );
            });
        }
        $("form button").hide();
        $("form input, form select").attr("disabled", "disabled");
        $("#status").text("Uploading file");
        $.ajax({
            xhr: function() {
                var xhr = new window.XMLHttpRequest();
                xhr.upload.addEventListener("progress", function(evt) {
                    if (evt.lengthComputable) {
                        $("#size").text(Math.round(evt.loaded / 1000) + " kB of " + Math.round(evt.total / 1000) + " kB");
                        var percentComplete = Math.round((evt.loaded / evt.total) * 100);
                        $(".progress").attr("value", percentComplete);
                        $("#status").text("Uploading file: " + percentComplete + "% complete");
                        if (percentComplete == 100) {
                            $("#status").text("Processing file, please wait.")
                        }

                    }
                }, false);
                return xhr;
            },
            type: 'POST',
            url: "/validator",
            data: formData,
            complete: function(){
                processing = false;
            },
            success: function(data){
                render_content(data, filename);
            },
            error: function(xhr) {
                $("#report").html(xhr.responseText);
                $(".progress").hide();
                $("#timer").hide();
                $("#status").text("Failed to upload file");
                mixpanel.track('Upload Failure', {
                    'elapsed': elapsed(),
                    'conference': conference,
                    'distinct_id': filename,
                    'size': filesize,
                    'error': $("#report").text()
                });
            },
            timeout: timeout * 1000,
            cache: false,
            contentType: false,
            processData: false
        });

        mixpanel.track('Upload Start', {
            'conference': conference,
            'distinct_id': filename,
            'size': filesize
        });
    });
});
function closeDetails() {
    const details = document.querySelectorAll("details");
    details.forEach(function(targetDetail) {
        targetDetail.removeAttribute("open");
    });
}
