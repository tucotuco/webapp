/*
 * Occurrence search result map.
 */

define([
  'jQuery',
  'Underscore',
  'mps',
  'map',
  'Backbone',
  'text!explore/occ/ResultMap.html'
], function ($, _, mps, map, Backbone, template) {
  return Backbone.View.extend({

    options: null,

    map: null,

    initialize: function (options, app) {
      var lat = options.lat ? parseFloat(options.lat) : 0;
      var lon = options.lon ? parseFloat(options.lon) : 0;
      this.app = app;
      this.markers = [];
    },

    render: function () {
      var marker = null;

      this.$el.html(_.template(template));

      if (!this.map) {
        if (!window.google || !window.google.maps) {
          return this;
        }
        //this.latlon = new google.maps.LatLng(lat, lon);
        this.options = {
          zoom: 2,
          center: new google.maps.LatLng(0, 0),
          mapTypeId: google.maps.MapTypeId.TERRAIN
        };
        this.map = new google.maps.Map(this.$('#map')[0], this.options);
        this.collection.on('add', this._updateMarkers, this);
        this.collection.on('reset', this._updateMarkers, this);
        this._updateMarkers();
      }
      //map = this.map;
      this.resize();

      return this;
    },

    _updateMarkers: function() {
      this.bounds = new google.maps.LatLngBounds();

      // Remove markers from map.
      _.each(this.markers, _.bind(function(marker) {
        marker.setMap(null);
      }, this));

      // Clear markers array.
      this.markers.splice(0, this.markers.length);

      _.each(this.collection.models, _.bind(function(model) {
        var lat = model.get('decimallatitude') ? parseFloat(model.get('decimallatitude')) : null;
        var lon = model.get('decimallongitude') ? parseFloat(model.get('decimallongitude')) : null;
        var sciname = model.get('scientificname') ? model.get('scientificname') : null;
        var year = model.get('year') ? parseInt(model.get('year')) : null;
        var country = model.get('country') ? model.get('country') : null;
        var stateprov = model.get('stateprovince') ? model.get('stateprovince') : null;
        var instcode= model.get('institutioncode') ? model.get('institutioncode') : null;
        var catalogno = model.get('catalognumber') ? model.get('catalognumber') : null;
        var occid = model.get('id') ? model.get('id') : null;
        var latlon = null;
        var marker = null;
        var contentString = null;
        var infowindow = null;
        
        if (lat && lon) { 
          latlon = new google.maps.LatLng(lat, lon);
          this.bounds.extend(latlon);
          // Create content for the infoWindow
          contentString = occid;
          // Create infoWindow
          infowindow = new google.maps.InfoWindow({
            title: occid,
            content : contentString
          });
          // Create marker
          marker = new google.maps.Marker({
            map: this.map,
            draggable: false,
            position: latlon,
            clickable: true,
            title: occid
          });

          // Listener to open the infowindow
          google.maps.event.addListener(marker, 'click', function() {
            infowindow.open(this.map,marker);
          });
          // Add marker to the array
          this.markers.push(marker);
        }
      }, this));
      this.resize();
    },

    resize: function() {
      google.maps.event.trigger(this.map, 'resize');
      this.map.setZoom(this.map.getZoom());
      this.map.setCenter(this.map.getCenter());
      this.map.setZoom(2);
      centerZero = new google.maps.LatLng(0, 0);
      this.map.setCenter(centerZero);
      if (this.markers.length != 0) {
        this.map.fitBounds(this.bounds);
      }
      console.log(this.map.getCenter().toString());
      console.log(this.map.getZoom().toString());
    }

  });
});