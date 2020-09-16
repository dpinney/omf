(function (global, factory) {
	typeof exports === 'object' && typeof module !== 'undefined' ? factory(exports) :
	typeof define === 'function' && define.amd ? define(['exports'], factory) :
	(global = global || self, factory(global['leaflet-kmz'] = {}));
}(this, (function (exports) { 'use strict';

	// import JSZip from 'jszip';
	// import * as toGeoJSON from '@tmcw/togeojson';

	function loadFile(url) {
		return new Promise((resolve, reject) => {
			let xhr = new XMLHttpRequest();
			xhr.open('GET', url);
			xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
			xhr.responseType = "arraybuffer";
			xhr.onload = () => {
				if (xhr.readyState === 4 && (xhr.status === 200 || xhr.status === 0)) {
					resolve(xhr.response || xhr.responseText);
				} else {
					console.warn("Error " + xhr.status + " while fetching remote file: " + url);
				}
			};
			xhr.onerror = () => reject("Error " + xhr.status + " while fetching remote file: " + url);
			xhr.send();
		});
	}

	function getKmlDoc(files) {
		return files["doc.kml"] ? "doc.kml" : getKmlFiles(Object.keys(files))[0];
	}

	function getKmlFiles(files) {
		return files.filter((file) => isKmlFile(file));
	}

	function getImageFiles(files) {
		return files.filter((file) => isImageFile(file));
	}

	function getFileExt(filename) {
		return filename.split('.').pop().toLowerCase().replace('jpg', 'jpeg');
	}

	function getFileName(url) {
		return url.split('/').pop();
	}

	function getMimeType(filename, ext) {
		var mime = 'text/plain';
		if (/\.(jpe?g|png|gif|bmp)$/i.test(filename)) {
			mime = 'image/' + ext;
		} else if (/\.kml$/i.test(filename)) {
			mime = 'text/plain';
		}
		return mime;
	}

	function isImageFile(filename) {
		return /\.(jpe?g|png|gif|bmp)$/i.test(filename);
	}

	function isKmlFile(filename) {
		return /.*\.kml/.test(filename);
	}

	/**
	 * It checks if a given file begins with PK, if so it's zipped
	 *
	 * @link https://en.wikipedia.org/wiki/List_of_file_signatures
	 */
	function isZipped(file) {
		return 'PK' === String.fromCharCode(new Uint8Array(file, 0, 1), new Uint8Array(file, 1, 1));
	}

	function lazyLoader(urls, promise) {
		return promise instanceof Promise ? promise : Promise.all(urls.map(url => loadJS(url)))
	}

	function loadJS(url) {
		return new Promise((resolve, reject) => {
			let tag = document.createElement("script");
			tag.addEventListener('load', resolve.bind(url), { once: true });
			tag.src = url;
			document.head.appendChild(tag);
		});
	}

	function parseLatLonBox(xml) {
		let box = L.latLngBounds([
			xml.getElementsByTagName('south')[0].childNodes[0].nodeValue,
			xml.getElementsByTagName('west')[0].childNodes[0].nodeValue
		], [
			xml.getElementsByTagName('north')[0].childNodes[0].nodeValue,
			xml.getElementsByTagName('east')[0].childNodes[0].nodeValue
		]);
		let rotation = xml.getElementsByTagName('rotation')[0];
		if (rotation !== undefined) {
			rotation = parseFloat(rotation.childNodes[0].nodeValue);
		}
		return [box, rotation];
	}

	function parseGroundOverlay(xml, props) {
		let [bounds, rotation] = parseLatLonBox(xml.getElementsByTagName('LatLonBox')[0]);
		let href = xml.getElementsByTagName('href')[0];
		let color = xml.getElementsByTagName('color')[0];
		let icon = xml.getElementsByTagName('Icon')[0];
		let options = {};
		if (!href && icon) {
			href = icon.getElementsByTagName('href')[0];
		}
		href = href.childNodes[0].nodeValue;
		href = props.icons[href] || href;
		if (color) {
			color = color.childNodes[0].nodeValue;
			options.opacity = parseInt(color.substring(0, 2), 16) / 255.0;
			options.color = '#' + color.substring(6, 8) + color.substring(4, 6) + color.substring(2, 4);
		}
		if (rotation) {
			options.rotation = rotation;
		}
		return new L.KMZImageOverlay(href, bounds, { opacity: options.opacity, angle: options.rotation });
	}

	function toGeoJSON(data, props) {
		var xml = data instanceof XMLDocument ? data : toXML(data);
		var json = window.toGeoJSON.kml(xml);
		json.properties = L.extend({}, json.properties, props || {});
		return json;
	}

	function toXML(data) {
		var text = data instanceof ArrayBuffer ? String.fromCharCode.apply(null, new Uint8Array(data)) : data;
		return (new DOMParser()).parseFromString(text, 'text/xml');
	}

	function unzip(folder) {
		return new Promise((resolve, reject) => {
			window.JSZip.loadAsync(folder)
				.then((zip) => {

					// Parse KMZ files.
					var files = Object.keys(zip.files)
						.map((name) => {
							var entry = zip.files[name];
							if (isImageFile(name)) {
								var ext = getFileExt(name);
								var mime = getMimeType(name, ext);
								return entry
									.async("base64")
									.then((value) => [name, 'data:' + mime + ';base64,' + value]);
							}
							return entry
								.async("text")
								.then((value) => [name, value]); // [ fileName, stringValue ]
						});

					// Return KMZ files.
					Promise.all(files).then((list) =>
						resolve(list.reduce((obj, item) => {
							obj[item[0]] = item[1]; // { fileName: stringValue }
							return obj;
						}, {}))
					);
				});
		});
	}

	const KMZLayer = L.KMZLayer = L.FeatureGroup.extend({
		options: {
			interactive: true,
			ballon: true,
			bindPopup: true,
			bindTooltip: true,
			preferCanvas: false,
		},

		initialize: function(kmzUrl, options) {
			L.extend(this.options, options);

			if (L.Browser.mobile) this.options.bindTooltip = false;

			this._layers = {};

			if (kmzUrl) this.load(kmzUrl);
		},

		add: function(kmzUrl) {
			this.load(kmzUrl);
		},

		load: function(kmzUrl) {
			L.KMZLayer._jsPromise = lazyLoader(this._requiredJSModules(), L.KMZLayer._jsPromise)
				.then(() => this._load(kmzUrl));
		},

		_load: function(url) {
			return loadFile(url).then((data) => this._parse(data, { name: getFileName(url), icons: {} }));
		},

		_parse: function(data, props) {
			return isZipped(data) ? this._parseKMZ(data, props) : this._parseKML(data, props);
		},

		_parseKMZ: function(data, props) {
			unzip(data).then((kmzFiles) => {
				var kmlDoc = getKmlDoc(kmzFiles);
				var images = getImageFiles(Object.keys(kmzFiles));

				var kmlString = kmzFiles[kmlDoc];
				// cache all images with their base64 encoding
				props.icons = images.reduce((obj, item) => {
					obj[item] = kmzFiles[item];
					return obj;
				}, {});

				this._parseKML(kmlString, props);
			});
		},

		_parseKML: function(data, props) {
			var xml = toXML(data);
			var geojson = toGeoJSON(xml, props);
			var layer = (this.options.geometryToLayer || this._geometryToLayer).call(this, geojson, xml);
			this.addLayer(layer);
			this.fire('load', { layer: layer, name: geojson.properties.name });
		},

		_geometryToLayer: function(data, xml) {
			var preferCanvas = this._map ? this._map.options.preferCanvas : this.options.preferCanvas;
			// parse GeoJSON
			var layer = L.geoJson(data, {
				pointToLayer: (feature, latlng) => {
					if (preferCanvas) {
						return L.kmzMarker(latlng, {
							iconUrl: data.properties.icons[feature.properties.icon] || feature.properties.icon,
							iconSize: [28, 28],
							iconAnchor: [14, 14],
							interactive: this.options.interactive,
						});
					}
					// TODO: handle L.svg renderer within the L.KMZMarker class?
					return L.marker(latlng, {
						icon: L.icon({
							iconUrl: data.properties.icons[feature.properties.icon] || feature.properties.icon,
							iconSize: [28, 28],
							iconAnchor: [14, 14],
						}),
						interactive: this.options.interactive,
					});
				},
				style: (feature) => {
					var styles = {};
					var prop = feature.properties;

					if (prop.stroke) {
						styles.stroke = true;
						styles.color = prop.stroke;
					}
					if (prop.fill) {
						styles.fill = true;
						styles.fillColor = prop.fill;
					}
					if (prop["stroke-opacity"]) {
						styles.opacity = prop["stroke-opacity"];
					}
					if (prop["fill-opacity"]) {
						styles.fillOpacity = prop["fill-opacity"];
					}
					if (prop["stroke-width"]) {
						styles.weight = prop["stroke-width"] * 1.05;
					}

					return styles;
				},
				onEachFeature: (feature, layer) => {
					if (!this.options.ballon) return;

					var prop = feature.properties;
					var name = prop.name || "";
					var desc = prop.description || "";

					if (name || desc) {
						if (this.options.bindPopup) {
							layer.bindPopup('<div>' + '<b>' + name + '</b>' + '<br>' + desc + '</div>');
						}
						if (this.options.bindTooltip) {
							layer.bindTooltip('<b>' + name + '</b>', {
								direction: 'auto',
								sticky: true,
							});
						}
					}
				},
				interactive: this.options.interactive,
			});
			// parse GroundOverlays
			let el = xml.getElementsByTagName('GroundOverlay');
			for (let l, k = 0; k < el.length; k++) {
				l = parseGroundOverlay(el[k], data.properties);
				if (l) {
					layer.addLayer(l);
				}
			}
			return layer;
		},

		_requiredJSModules: function() {
			var urls = [];
			var host = 'https://unpkg.com/';

			if (typeof window.JSZip !== 'function') {
				urls.push(host + 'jszip@3.5.0/dist/jszip.min.js');
			}
			if (typeof window.toGeoJSON !== 'object') {
				urls.push(host + '@tmcw/togeojson@4.1.0/dist/togeojson.umd.js');
			}

			return urls;
		},
	});

	L.kmzLayer = function(url, options) {
		return new L.KMZLayer(url, options);
	};

	/**
	 * Optimized leaflet canvas renderer to load numerous markers
	 *
	 * @link https://stackoverflow.com/a/51852641
	 * @link https://stackoverflow.com/a/43019740
	 *
	 */
	L.KMZMarker = L.CircleMarker.extend({
		// initialize: function(latlng, options) {
		// 	L.CircleMarker.prototype.initialize.call(this, latlng, options);
		// },
		_updatePath: function() {
			var renderer = this._renderer;
			var icon = this._icon;
			var layer = this;

			if (!renderer._drawing || layer._empty()) {
				return;
			}

			// if (icon.complete)
			if (icon) {
				icon.drawImage();
			} else {
				icon = this._icon = new Image(this.options.iconSize[0], this.options.iconSize[1]);
				icon.anchor = [icon.width / 2.0, icon.height / 2.0];
				icon.onload = icon.drawImage = () => {
					var p = layer._point.subtract(icon.anchor);
					var ctx = renderer._ctx;

					ctx.drawImage(icon, p.x, p.y, icon.width, icon.height);

					// Removed in Leaflet 1.4.0
					// if (renderer._drawnLayers) renderer._drawnLayers[layer._leaflet_id] = layer;
					// else renderer._layers[layer._leaflet_id] = layer;
				};
				icon.src = this.options.iconUrl;
			}
		}
	});

	L.kmzMarker = function(ll, opts) {
		return new L.KMZMarker(ll, opts);
	};

	var KMZMarker = L.KMZMarker;

	/**
	 * Copyright (c) 2011-2015, Pavel Shramov, Bruno Bergot - MIT licence
	 *
	 * adapted from: https://github.com/windycom/leaflet-kml/L.KML.js
	 */
	L.KMZImageOverlay = L.ImageOverlay.extend({
		options: {
			angle: 0
		},
		_reset: function() {
			L.ImageOverlay.prototype._reset.call(this);
			this._rotate();
		},
		_animateZoom: function(e) {
			L.ImageOverlay.prototype._animateZoom.call(this, e);
			this._rotate();
		},
		_rotate: function() {
			if (L.DomUtil.TRANSFORM) {
				// use the CSS transform rule if available
				this._image.style[L.DomUtil.TRANSFORM] += ' rotate(' + this.options.angle + 'deg)';
			} else if (L.Browser.ie) {
				// fallback for IE6, IE7, IE8
				var rad = this.options.angle * (Math.PI / 180),
					costheta = Math.cos(rad),
					sintheta = Math.sin(rad);
				this._image.style.filter += ' progid:DXImageTransform.Microsoft.Matrix(sizingMethod=\'auto expand\', M11=' +
					costheta + ', M12=' + (-sintheta) + ', M21=' + sintheta + ', M22=' + costheta + ')';
			}
		},
		getBounds: function() {
			return this._bounds;
		}
	});

	exports.KMZLayer = KMZLayer;
	exports.KMZMarker = KMZMarker;

	Object.defineProperty(exports, '__esModule', { value: true });

})));
//# sourceMappingURL=leaflet-kmz-src.js.map