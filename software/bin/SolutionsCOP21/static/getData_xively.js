function getNewDashboardData() {
    $.ajax({
        url:            'https://api.xively.com/v2/feeds/918651241',
        dataType:       'json',
        headers:  {
            'X-ApiKey': 'VALDxWNsi0roJQNtrFmCB3mBRBNgqeOAMlag1VcvkAd7peKp'
        },
        success:        xively_cb
    });
}

function xively_cb(xivelyData) {
    ts             = xivelyData['datastreams'][0]['at']
    tempPerMote    = xivelyData['datastreams'][0]['current_value'].split('_')
    temperature    = {}
    for (var i=0;i<tempPerMote.length;i++) {
        mac        = tempPerMote[i].split(':')[0]
        temp       = tempPerMote[i].split(':')[1]
        temperature[mac] = [temp,ts]
    }
    newData = {
        'paths':        {},
        'temperature':  temperature,
    }
    refreshDashboard_cb(newData);
}