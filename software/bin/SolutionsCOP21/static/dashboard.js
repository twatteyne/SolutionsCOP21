//========== setup

// make sure IE does not return cached results.
jQuery.ajaxSetup({ cache: false });

//========== defines

var map_w          = 0;
var map_h          = 0;
var map_top        = 0;
var map_left       = 0;

/*
  +-7-----8-+-9----10-+
  6         |        11
  |         |         |
  5         |        12
  +--------M+---------+
  4         |        13
  |         |         |
  3         |        14
  +-2-----1-+---------+
*/

var positions      = {
    '00-17-0d-00-00-38-06-67': [0.45,0.50],      // position M
    
    '00-17-0d-00-00-38-06-ad': [0.40,0.89],      // position 1
    '00-17-0d-00-00-38-05-da': [0.20,0.89],      // position 2
    
    '00-17-0d-00-00-33-33-33': [0.05,0.80],      // position 3
    '00-17-0d-00-00-44-44-44': [0.05,0.60],      // position 4
    '00-17-0d-00-00-55-55-55': [0.05,0.40],      // position 5
    '00-17-0d-00-00-66-66-66': [0.05,0.20],      // position 6
    
    '00-17-0d-00-00-77-77-77': [0.20,0.13],      // position 7
    '00-17-0d-00-00-88-88-88': [0.40,0.13],      // position 8
    '00-17-0d-00-00-99-99-99': [0.60,0.13],      // position 9
    '00-17-0d-00-00-aa-aa-aa': [0.80,0.13],      // position 10
    
    '00-17-0d-00-00-bb-bb-bb': [0.95,0.20],      // position 11
    '00-17-0d-00-00-cc-cc-cc': [0.95,0.40],      // position 12
    '00-17-0d-00-00-dd-dd-dd': [0.95,0.60],      // position 13
    '00-17-0d-00-00-ee-ee-ee': [0.95,0.80]       // position 14
}

//=========================== admin ===========================================

function initDashboard() {
    
    //=== logo
    
    /*
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
    */
    
    //=== map
    
    if ($(window).width()>$(window).height()) {
        map_w      = $(window).height();
        map_h      = $(window).height();
    } else {
        map_w      = $(window).width();
        map_h      = $(window).width();
    }
    map_top        = ($(window).height()-map_h)/2;
    map_left       = ($(window).width()-map_w)/2;
    
    $('\
        <img id="map" src="map.jpg">'
    ).appendTo('#dashboard');
    $('#map').attr({
        'width':   map_w,
        'height':  map_h,
    });
    $('#map').offset(
        {
            top:  map_top,
            left: map_left
        }
    );
    
    svgText        = '<svg id="dashboardcanvas" xmlns="http://www.w3.org/2000/svg">'
    for (var mac in positions) {
        svgText   += '<circle id="'+mac+'_circle" class="mote"></circle>';
    }
    svgText       += '</svg>'
    $(svgText).appendTo('#dashboard');
    
    $('#dashboardcanvas').attr({
        'width':   map_w,
        'height':  map_h
    });
    $('#dashboardcanvas').offset(
        {
            top:  map_top,
            left: map_left
        }
    );
    
    //=== motes
    for (var mac in positions) {
        $('#'+mac+'_circle').attr({
            'cx':      positions[mac][0]*map_w,
            'cy':      positions[mac][1]*map_h
        });
        $('#'+mac).css({
            'z-index': -1
        });
    }
}

function refreshDashboard() {
   /*
   The following function is implemented in getData_local.js or getData_xively.js.
   It calls back refreshDashboard_cb() once it receives new data.
   */
   getNewDashboardData();
}
function refreshDashboard_cb(newData) {
    
    /*
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
    */
    // log
    console.log(newData);
}
