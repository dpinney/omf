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

var svg = d3.select("#chart")
  .append("svg")
  .attr("width", w)
  .attr("height", h)
  .on("click", onClickCanvas);

var force;
var link;
var node;
var root;

var sim_iter = 0;
var max_iter = 0;
var base_grav = 0.09;
var link_dist = 13;
var charge = -18;
var grav = 0;

var color = d3.scale.category20();

if(!model_id) {
  var split_path = window.location.pathname.split('');
  model_id = split_path[split_path.length-1];
}

d3.json("/api/models/" + model_id + ".json", function(json) {
  root = json;
  // for every 100 nodes, add a bit of gravity to keep nodes in the view
  var grav = base_grav + (json.nodes.length / 100) * 0.01;
  // run the layout sim based on the number of nodes 
  max_iter = 75;
  if(json.nodes.length < 50) {
    max_iter = 25;
  }
  if(json.nodes.length > 1000) {
    max_iter = 125;
  }
  force = d3.layout.force()
    .gravity(grav)
    .charge(charge)
    .linkDistance(link_dist)
    .nodes(json.nodes)
    .links(json.links)
    .size([w, h]);

  addLinks(json.links);
  addNodes(json.nodes);

  force.start();

  force.on("tick", onTick);
});


function onClickCanvas() {
  point = d3.mouse(this);
  addNewNode({name:"new",type:"new",group:4,x:point[0],y:point[1],fixed:1});
}

function onNodeover(t, i) {
  d3.select(this)
    .select("circle")
    .attr("r", "8")
    .style("stroke", "rgb(204,102,51)");
}

function onNodeout(t, i){
  d3.select(this)
    .select("circle")
    .attr("r", "5")
    .style("stroke")
    .remove();
}

function onTick() {
  sim_iter = sim_iter + 1;
  if(sim_iter % 5 == 0) {
    newwidth = ~~(100 * sim_iter / max_iter);
    $("#progress_bar").css("width", newwidth + "%");
  }

  if(sim_iter >= max_iter) {
    force.stop();
    haltNodeMovement();
    link.attr("x1", function(d) { return d.source.x; })
        .attr("y1", function(d) { return d.source.y; })
        .attr("x2", function(d) { return d.target.x; })
        .attr("y2", function(d) { return d.target.y; });

    node.attr("cx", function(d) { return d.x; })
        .attr("cy", function(d) { return d.y; });

    // node.attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });

    // show the chart and remove the progress
    $("#progress").hide();
    $("#chart").show();
  }

  // link.attr("x1", function(d) { return d.source.x; })
  //     .attr("y1", function(d) { return d.source.y; })
  //     .attr("x2", function(d) { return d.target.x; })
  //     .attr("y2", function(d) { return d.target.y; });

  // node.attr("cx", function(d) { return d.x; })
  //     .attr("cy", function(d) { return d.y; });
}

function addNewNode(d) {
  force.nodes().push(d);
  last_n = force.nodes().length-1;
  force.links().push({source:last_n,target:last_n-1,value:4});
  force.stop();
  addLinks(force.links());
  addNodes(force.nodes());
  force.start();
}

function addNodes(data) {
  node = svg.selectAll("circle.node").data(data)
  node
    .enter()
      .append("circle")
      .attr("class", "node")
      .attr("cx", function(d) { return w/2; })
      .attr("cy", function(d) { return h/2; })
      .attr("r", 5)
      .style("fill", function(d) { return color(d.group); })
      .call(force.drag);
  node
    .exit()
      .remove();

  node.append("title")
      .text(function(d) { return d.name; });
}

function addLinks(data) {
  link = svg.selectAll("line.link").data(data)
  link
    .enter()
      .append("line")
      .attr("class", "link")
      .style("stroke-width", function(d) { return Math.sqrt(d.value); });
  link
    .exit()
      .remove();
}