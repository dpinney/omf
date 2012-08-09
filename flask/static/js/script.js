/* Author: Aaron Perrin

*/

function addObject(obj_type) {
  console.log(obj_type)
}

$().ready(function(){ 
  var url = '/api/objects';
  $.getJSON(url, function(data) {
    $.each(data, function(key, val) {
      $('#object-types')
        .append($('<a>', { href : "Javascript: addObject(" + val + ");" })
          .text(val)
        );
      });
  });
});

 var w = 1000,
    h = 600,
    fill = d3.scale.category20();

var vis = d3.select("#chart")
  .append("svg:svg")
    .attr("width", w)
    .attr("height", h);

function toggleChildrenVis(node) {
  if (node.children) {
    node._children = node.children;
    node.children = null;
  } else {
    node.children = node._children;
    node._children = null;
  }
}

function click(d) {
  toggleChildrenVis(d);
  updateView(root);
}

function nodeover(t, i) {
  d3.select(this)
    .select("circle")
    .attr("r", "8")
    .style("stroke", "rgb(204,102,51)");
}

function nodeout(t, i){
  d3.select(this)
    .select("circle")
    .attr("r", "5")
    .style("stroke")
    .remove();
}

var root;

var split_path = window.location.pathname.split('');
var model_id = "large";
if(split_path.length > 1) {
  console.log(split_path);
  model_id = split_path[split_path.length-1];
}
d3.json("/api/models/" + model_id + ".json", function(json) {
  root = json;
  jQuery(json.nodes).each(function() {
    element = jQuery(this);
    element.attr({ x: w/2, y: h/2, px: w/2, py: h/2});
  });
  jQuery(json.links).each(function() {
    element = jQuery(this);
    element.attr({ x: w/2, y: h/2, px: w/2, py: h/2});
  });
  updateView(root);
});

function updateView(json) {

  var force = d3.layout.force()
    .charge(-10)
    .gravity(0.15)
    .linkDistance(13)
    .nodes(json.nodes)
    .links(json.links)
    .size([w, h])
    .start();

  var link = vis.selectAll("line.link")
    .data(json.links)
    .enter().append("svg:line")
    .attr("class", "link")
    .style("stroke-width", function(d) { return Math.sqrt(d.value); });

  var node = vis.selectAll("g.node")
    .data(json.nodes)
    .enter().append("svg:g")
    .attr("class", "node")
    .on("mouseover", nodeover)
    .on("mouseout", nodeout);

  	node.append("svg:circle")
      .attr("r", 5)
      .style("fill", function(d) { return fill(d.group); })
      .call(force.drag);

  vis.style("opacity", 1e-6)
    .transition()
      .duration(1000)
      .style("opacity", 1);

  var i = 0;
  force.on("tick", function() {
    i = i + 1;
    if(i % 5 == 0) {
      newwidth = ~~(100 * i / 150);
      $("#progress_bar").css("width", newwidth + "%");
    }
    if(i >= 150) {
      force.stop();
      link.attr("x1", function(d) { return d.source.x; })
          .attr("y1", function(d) { return d.source.y; })
          .attr("x2", function(d) { return d.target.x; })
          .attr("y2", function(d) { return d.target.y; });
      node.attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });
      // show the chart and remove the progress
      $("#progress").hide();
      $("#chart").show();
    }
  });
}