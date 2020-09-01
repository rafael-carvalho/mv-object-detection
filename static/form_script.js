$( document ).ready(function() {

    $('.triggers').change(function() {
      sequence = parseInt($(this).attr('data-sequence'));
      $('.triggers').each(function() {
      console.log($(this));
        seq = parseInt($(this).attr('data-sequence'));
        console.log($(this).prop('type'))
        if (seq > sequence) {
            $(this).prop('disabled', true);
            $(this).prop('required', false);
            if ($(this).prop('type') == 'select-one')  {
                $(this).empty();
            }
        } else {
            $(this).prop('disabled', false);
            $(this).prop('required', true);
        }
      });
    });



    $("#showhide").click(function()
     {
        if ($(this).data('val') == "1")
        {
           $("#api_key").prop('type','text');
           $("#eye").attr("class","glyphicon glyphicon-eye-close");
           $(this).data('val','0');
        }
        else
        {
           $("#api_key").prop('type', 'password');
           $("#eye").attr("class","glyphicon glyphicon-eye-open");
           $(this).data('val','1');
        }
     });

    $( "#form" ).submit(function( event ) {
      event.preventDefault();

      var selectedCountry = $(this).children("option:selected").val();

      var formData = {
          api_key: $('input[name=api_key]').val(),
          organization_id: $("#organizations").children("option:selected").val(),
          network_id: $("#networks").children("option:selected").val(),
          camera_serial: $("#cameras").children("option:selected").val(),
      };
      
      var feedback = null;

      $.ajax({
            type: 'POST',
            url: $(this).prop('action'),
            dataType : "json",
            data: JSON.stringify(formData),
            contentType: "application/json",
            beforeSend: function() {
                console.log('[START]')

                console.log(formData)
                $('#btn').prop('disabled', true);
                $('#loading').show();
            },
            success: function(data) {
                feedback = 'Success!'
                console.log(data.stage)
                if (data.stage) {
                    $('#' + data.stage).empty(); // remove old options
                    console.log(data.options)
                    data.options.forEach(function(option) {
                        console.log(option)
                        new_element = $("<option></option>");
                        console.log(new_element);
                        $(new_element).attr("value", option.id)
                        $(new_element).text(option.name)
                        if (option.disabled) {
                            $(new_element).attr('disabled', 'disabled')
                        }
                        $('#' + data.stage).append(new_element);
                    });
                    $('#' + data.stage).prop( "disabled", '' )
                    $('#' + data.stage).prop( "required", true)
                }
                if (data.next) {
                    //$('#btn').text(data.next)
                } else {
                    console.log(data.rtsp_link)
                    var weights = $('#model').val()
                    var confidence_threshold = $('#confidence_threshold').val()

                    startStream(data.rtsp_link, weights, confidence_threshold);
                    request_classes(weights)
                }

                btn_options = ['btn-secondary', 'btn-primary', 'btn-warning', 'btn-success', 'btn-info', ]

                for (i=0; i < btn_options.length; i++) {
                    option = btn_options[i]
                    if ($('#btn').hasClass(option)) {
                        $('#btn').removeClass(option);
                        $('#btn').addClass(btn_options[(i + 1) % btn_options.length])
                        break;
                    }
                }
            },
            error: function(xhr) {
                feedback = 'Something wrong happened'
            },
            complete: function() {
                $('#btn').prop('disabled', false);
                $('#loading').hide();
                console.log(feedback)
            }
        });
    });

    //$('#btn').click();
});

function startStream(rtsp_link, weights, confidence_threshold) {
    $('#stream').attr('src', "")
    $('#stream_parent').show();
    $('#rtsp_link').text(rtsp_link);
    $('#model_name').text(weights)
    $('#confidence_threshold_name').text(confidence_threshold + '%')
    url = '/video_feed' + '/weights/' + weights + '/confidence/' + (parseInt(confidence_threshold) / 100) + '/link/' + rtsp_link
    console.log(url)
    $('#stream').attr('src', encodeURI(url))

}

function request_classes(weights) {
    url = '/classes/' + weights
    url = encodeURI(url)
    $.ajax({
            type: 'GET',
            url: url,
            dataType : "json",
            data: null,
            contentType: "application/json",
            beforeSend: function() {
                console.log('[START]')
                console.log(url)

            },
            success: function(data) {
                console.log(data)
                classes = data.classes
                column_len = 10
                classes = chunkArray(classes, column_len)
                feedback = 'Class load success!'

                $('#classes_container').show();
                $('#classes').empty()


                for (i = 0; i < classes.length; i++) {
                    var ul = $('<ul class="col" style="list-style: none;" />');
                    for (j = 0; j < classes[i].length; j++) {
                        ul.append('<li>' + classes[i][j] + '</li>')
                    }
                    $('#classes').append(ul)

                }
                console.log(data.classes)
            },
            error: function(xhr) {
                feedback = 'Something wrong happened'
            },
            complete: function() {
                $('#btn').prop('disabled', false);
                $('#loading').hide();
                console.log(feedback)
            }
    });

}

/**
 * Returns an array with arrays of the given size.
 *
 * @param myArray {Array} array to split
 * @param chunk_size {Integer} Size of every group
 */
function chunkArray(myArray, chunk_size){
    var index = 0;
    var arrayLength = myArray.length;
    var tempArray = [];

    for (index = 0; index < arrayLength; index += chunk_size) {
        myChunk = myArray.slice(index, index+chunk_size);
        // Do something if you want with the group
        tempArray.push(myChunk);
    }

    return tempArray;
}