//========== setup

// make sure IE does not return cached results.
jQuery.ajaxSetup({ cache: false });

//========== defines

var safezone_cx    = 0;
var safezone_cy    = 0;
var safezone_r     = 0;
var lastUpdate     = 0;

//=========================== admin ===========================================

function initDashboard() {
    
    //=== logo
    
    $('\
        <div id="logo" class="logo"> \
            <img src="logo.png">\
        </div>'
    ).appendTo('#dashboard');
    $('#logo').offset(
        {
            top:  $(window).height()-61-20,
            left: $(window).width()-200-20
        }
    );
    $('#logo').css('z-index',-1);
    
    //=== safezone
    
    safezone_cx    = $(window).width()/2;
    safezone_cy    = $(window).height()/2;
    safezone_r     = Math.min($(window).width(),$(window).height())/2.5;
    
    $('\
        <svg id="dashboardcanvas" xmlns="http://www.w3.org/2000/svg">\
            <circle id="safezone"/> \
            <line   id="lineh" class="safezoneline" x1="0" y1="0" x2="200" y2="200"/> \
            <line   id="linev" class="safezoneline" x1="0" y1="0" x2="200" y2="300"/> \
            <circle id="dot"/> \
        </svg>'
    ).appendTo('#dashboard');
    $('#dashboardcanvas').attr({
        'width':   $(window).width()-20,
        'height':  $(window).height()-20
    });
    $('#safezone').attr({
        'cx':      safezone_cx,
        'cy':      safezone_cy,
        'r':       safezone_r,
        'fill':    "#c0c0c0"
    });
    $('#linev').attr({
        'x1':      safezone_cx,
        'y1':      safezone_cy-safezone_r,
        'x2':      safezone_cx,
        'y2':      safezone_cy+safezone_r
    });
    $('#lineh').attr({
        'x1':      safezone_cx-safezone_r,
        'y1':      safezone_cy,
        'x2':      safezone_cx+safezone_r,
        'y2':      safezone_cy
    });
    $('#dot').attr({
        'cx':      -50,
        'cy':      -50
    });
    $('#dot').css({
        'z-index': -1
    });
}

function refreshDashboard() {
   /*
   The following function is implemented in getData_local.js or getData_xively.js.
   It calls back refreshDashboard_cb() once it receives new data.
   */
   getNewDashboardData();
}
function refreshDashboard_cb(newData) {
    
    // filter cases when I don't need to update
    if (newData['calibrated']==false) {
        return;
    }
    if (newData['lastUpdate']==lastUpdate) {
        return;
    }
    
    // remember when I updated last
    lastUpdate = newData['lastUpdate'];
    
    // toggle color dot
    if ($('#dot').attr('fill')=="#de9118") {
        $('#dot').attr('fill',"#ffa71c");
    } else {
        $('#dot').attr('fill',"#de9118");
    }
    
    // reposition dot
    $('#dot').attr({
        'cx':      safezone_cx+safezone_r*newData['radius']*Math.sin(newData['heading']),
        'cy':      safezone_cy-safezone_r*newData['radius']*Math.cos(newData['heading'])
    });
    
    // warn if radius too large
    if (newData['radius']>1.0) {
        $('#safezone').attr('fill',"#ff0000");
        var audio = new Audio('sound.mp3');
        audio.play();
    } else {
        $('#safezone').attr('fill',"#5ea00f");
    }
    
    // log
    console.log(newData);
}
