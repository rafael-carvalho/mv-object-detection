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
                    startStream(data.rtsp_link);
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

function startStream(rtsp_link) {
    $('#stream').attr('src', encodeURI('/video_feed/' + rtsp_link))
}