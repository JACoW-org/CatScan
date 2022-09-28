var startTime;
var processing = false;
var timeout = 60;
function start() {
    startTime = new Date();
};
function elapsed() {
    endTime = new Date();
    var timeDiff = endTime - startTime;
    timeDiff /= 1000;
    return Math.round(timeDiff);
}

$(document).ready(function(){
    const file = document.getElementById("file");
    file.onchange = function(){
        if(file.files.length > 0) {
          document.getElementById('filename').innerHTML = file.files[0].name;
          let extension = file.files[0].name.split('.').pop();
          if (extension != 'docx' && extension != 'tex') {
            $(".file").addClass("is-danger");
            $(".file span.file-label").text("Must be .docx or .tex");
            $("form button[type=submit]").attr("disabled", "disabled");
          }
          else {
              $(".file").removeClass("is-danger");
              $(".file span.file-label").text("Choose a file…");
              $("form button[type=submit]").removeAttr("disabled");
          }
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
                $("#report").html(data);
                $("#upload-form").hide();

                mixpanel.track('Upload Success', {
                    'elapsed': elapsed(),
                    'conference': conference,
                    'distinct_id': filename,
                    'size': filesize
                });

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
                    'error': $("#report #error").text()
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
