function getCheckedRadioValue(name) {
    var elements = document.getElementsByName(name);

    for (var i=0, len=elements.length; i<len; ++i)
        if (elements[i].checked) return elements[i].value;
};

function set_active(name) {
    $("top_nav").each(function(){
        $(this).classList.add('active');
    });
    document.getElementById(name).classList.remove('active');
}

function opentab(tabname) {
  // hide all divs
  var tabcontent = document.getElementsByClassName("tabcontent");
  for (var i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }
  // set all tabs to "not selected"
  var tablinks = document.getElementsByClassName("tablinks active");
  for (var i = 0; i < tablinks.length; i++) {
    tablinks[i].className = tablinks[i].className.replace(" active", "");
  }
  document.getElementById(tabname).style.display = "block"; // make corresponding div visible
  var tabname_button = tabname + "_button"
  document.getElementById(tabname_button).className += " active"; // select tab in the tab menu
}

function submit() {
    arr = [];
    for (var i=1, n_questions=38; i<=n_questions; ++i) { // TODO: variable number of questions
        answer_name = "answer" + i;
        arr.push(getCheckedRadioValue(answer_name));
    }; 
    console.log(arr);
    //$.post("/check_selected", JSON.stringify({abc: 1}));//JSON.stringify(arr))
    //console.log("a")

    /*
    console.log(JSON.stringify(arr));

    var url = "/evaluate";
    var params = JSON.stringify(arr);
    var xhr = new XMLHttpRequest();
    xhr.open("POST", url, true);

    //Send the proper header information along with the request
    xhr.setRequestHeader("Content-Type", "application/json");

    xhr.send(JSON.stringify(arr));
    */
    

    var saveData = $.ajax({
        type: "POST",
        url: "/evaluate",
        //action: "{{ url_for('predict') }}",
        data: JSON.stringify(arr),
        contentType: 'application/json;charset=UTF-8',
        success: function() {   
            location.reload();  
        }
    });
    

/*
    $.postJSON('/check_selected', {
        results: JSON.stringify(arr)
        }, function(data) {
            var response = data.result;
            console.log(response);
            }
    );
    */
    //$('#delay_label').text((slider_value / 1000.0).toFixed(1));
    //var xhttp = new XMLHttpRequest();
    //xhttp.open("POST", "/check_selected" + slider_value, true);
    //xhttp.send();
};

