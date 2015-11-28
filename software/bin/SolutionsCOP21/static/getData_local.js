function getNewDashboardData() {
   $.ajax({
      url:      '/data.json',
      dataType: 'json',
      success:  refreshDashboard_cb
   });
}
