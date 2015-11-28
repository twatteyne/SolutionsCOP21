function getNewDashboardData() {
    $.ajax({
        url:            'https://api.xively.com/v2/feeds/1858382421',
        dataType:       'json',
        headers:  {
            'X-ApiKey': 'bStJkeooJSfJUJ5YfYWKASHYl8yLeq0D6IlLC2lT22C2zqQ1'
        },
        success:        xively_cb
    });
}

function xively_cb(xivelyData) {
    newData = {
        'calibrated':   true,
        'lastUpdate':   xivelyData['datastreams'][0]['at'],
        'radius':       xivelyData['datastreams'][1]['current_value'],
        'heading':      xivelyData['datastreams'][0]['current_value'],
    }
    refreshDashboard_cb(newData);
}