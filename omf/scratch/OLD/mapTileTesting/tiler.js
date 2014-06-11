d3.geo.tiler = function() {
	var tiler = {},
			points = [],
			// TODO: this mercator is not covered in d3.v3.js, it's in d3.geo
			projection = d3.geo.mercator().scale(1).translate([.5, .5]),
			location = Object, // identity function
			zoom = 8,
			root = null;

	function build(points, x, y, z) {
		if (z >= zoom) return points.map(d3_geo_tilerData);
		var i = -1,
				n = points.length,
				c = [[], [], [], []],
				k = 1 << z++,
				p;
		while (++i < n) {
			p = points[i];
			var x1 = (p[0] * k - x) >= .5,
					y1 = (p[1] * k - y) >= .5;
			c[x1 << 1 | y1].push(p);
		}
		x <<= 1;
		y <<= 1;
		return {
			"0": c[0].length && build(c[0], x    , y    , z),
			"1": c[1].length && build(c[1], x    , y + 1, z),
			"2": c[2].length && build(c[2], x + 1, y    , z),
			"3": c[3].length && build(c[3], x + 1, y + 1, z)
		};
	}

	tiler.location = function(x) {
		if (!arguments.length) return location;
		location = x;
		root = null; // reset
		return tiler;
	};

	tiler.projection = function(x) {
		if (!arguments.length) return projection;
		projection = x;
		root = null; // reset
		return tiler;
	};

	tiler.zoom = function(x) {
		if (!arguments.length) return zoom;
		zoom = x;
		root = null; // reset
		return tiler;
	};

	tiler.points = function(x) {
		if (!arguments.length) return points;
		points = x;
		root = null; // reset
		return tiler;
	};

	tiler.tile = function(x, y, z) {
		var results = [];

		// Lazy initialization…
		// Project the points to normalized coordinates in [0, 1].
		if (!root) {
			root = build(points.map(function(d, i) {
				// TODO: Debug here. The projection function is in d3.geo.js function mercator(coordinates)
				// coordinates should indicate latitude and longitude as an array.
				var point = projection(location.call(tiler, d, i));
				point.data = d,point;
				return point;
			}), 0, 0, 0);
		}

		function search(node, x0, y0, z0) {
			if (!node) return;
			if (z0 < z) {
				var k = Math.pow(2, z0 - z),
						x1 = (x * k - x0) >= .5,
						y1 = (y * k - y0) >= .5;
				// console.log(node[x1 << 1 | y1])
				search(node[x1 << 1 | y1], x0 << 1 | x1, y0 << 1 | y1, z0 + 1);
			} else {
				accumulate(node);
			}
		}

		function accumulate(node) {
			if (node.length) {
				for (var i = -1, n = node.length; ++i < n;) {
					results.push(node[i]);
				}
			} else {
				for (var i = -1; ++i < 4;) {
					if (node[i]) accumulate(node[i]);
				}
			}
		}

		search(root, 0, 0, 0);
		return results;
	};

	return tiler;
};

function d3_geo_tilerData(d) {
	return d.data;
}

