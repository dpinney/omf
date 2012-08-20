/* Author: Aaron Perrin

*/

function addNewObject(obj_type) {
  $('#modal_insert').load('/api/modeltemplates/' + obj_type + '.html', function() {
    $('#modal').modal();
    // put it in a random posiiton in the top left portion of the view
    x1 = 10 + w * .2 * Math.random();
    y1 = 10 + w * .2 * Math.random();
    newObj = {x: x1, y: y1, group:9, index: force.nodes().length, weight:1};
    $('#modal_accept')
      .on('click', function() {
        $.each($('#modal_form input'), function(i, v) {
          if(v.id === "name") {
            newObj['name'] = v.value;
          }
          else {
            newObj['_' + v.id] = v.value;
          }
        });
        addNewNode(newObj);
        $('#modal').modal('hide');
        $('#modal').remove();
      });
    $('#modal').modal('show');
  });
}

$().ready(function(){ 
  var url = '/api/objects';
  $.getJSON(url, function(data) {
    $.each(data, function(key, val) {
      $('#object-types')
        .append($('<a>', { href : "Javascript: addNewObject('" + val + "');" })
          .text(val)
        );
      });
  });
});

// Huge hack to get the height where we put the svg...

var w = $('body').width(),
    h = $(window).height() - $('body').height() - 4;

var svg = d3.select("#chart")
  .append("svg")
  .attr("width", w)
  .attr("height", h);

var node_radius = 5;
var sim_iter = 0;
var max_iter = 0;
var base_grav = 0.09;
var link_dist = 20;
var charge = -18;
var grav = 0;
var link_weight = 2;
var color = d3.scale.category10();

var force;
var link;
var node;
var root;

if(!model_id) {
  var split_path = window.location.pathname.split('');
  model_id = split_path[split_path.length-1];
}

d3.json("/api/models/" + model_id + ".json", function(json) {
  root = json;
  // for every 100 nodes, add a bit of gravity to keep nodes in the view
  var grav = base_grav + (json.nodes.length / 100) * 0.003;
  // run the layout sim based on the number of nodes 
  max_iter = 75;
  if(root.nodes.length < 50) {
    max_iter = 25;
  }
  if(root.nodes.length > 1000) {
    max_iter = 125;
  }
  force = d3.layout.force()
    .gravity(grav)
    .charge(charge)
    .linkDistance(link_dist)
    .nodes(root.nodes)
    .links(root.links)
    .size([w, h]);
  force.start();

  updateLinkView();
  updateNodeView();

  force.on("tick", onTick);
});

function editObject(d_index) {
  d = root.nodes[d_index];
  $('#modal_insert').load('/api/modeltemplates/default.html', function() {
    $('#modal').modal();
    $('#type_title').replaceWith('<h2>Edit ' + d.name + '</h2>');
    jQuery.each(d, function(prop, value) {
      if(prop.charAt(0) === '_') {
        var label = prop.substring(1, prop.length);
        $('#modal_form').append(' \
            <div class="control-group"> \
              <label class="control-label" for="' + label + '">' + label + '</label> \
              <div class="controls"> \
                <input type="text" class="input-xlarge" id=' + label + ' value="' + value + '"></input> \
              </div> \
            </div>'
          );
        }
    });

    $('#modal_accept')
      .on('click', function() {
        d = root.nodes[d_index];
        $.each($('#modal_form input'), function(i, v) {
          if(v.id === "name") {
            d['name'] = v.value;
          }
          else {
            d['_' + v.id] = v.value;
          }
        });
        selectNode(d);
        $('#modal').modal('hide');
        $('#modal').remove();
      });
    $('#modal').modal('show');
  });
}

function selectNode(d) {
    // visually mark the node
  selected = d;
  // hack: if the 'highlight' comes first, it overshadows the selection
  classify(d, "highlighted", false); 
  classify(d, "selected", true);

  // clear the selected table
  $('#selected tbody')
    .empty();

  for(var prop in d) {
    // 'real' properties are stored with an underscore
    if(prop[0] === '_') {
      $('#selected tbody')
        .append('<tr><td>' + prop.substring(1, prop.length) + '</td><td>' + d[prop] +'</td></tr>');
    }
  }
  $('#selected tbody')
    .append('<tr><td colspan="2"><a class="btn" href="Javascript: editObject(' + d.index + ');" }>Edit</button></td></tr>');
}

function onNodeclick(d, i) {
  selectNode(d);
}

function onNodeover(d, i) {
  classify(d, "highlighted", true);
}

function onNodeout(d, i) {
  classify(d, "highlighted", false);
}

function classify(d, c, on) {
  if(on) {
    // turn off the currently styled one
    svg.select("." + c).classed(c, false);
    // then, style the new one
    svg.select("#n" + d.index).classed(c, true);
  }
  else {
    svg.select("#n" + d.index).classed(c, false);
  }
}

function onTick() {
  sim_iter = sim_iter + 1;
  if(sim_iter % 5 == 0) {
    newwidth = ~~(100 * sim_iter / max_iter);
    $("#progress_bar").css("width", newwidth + "%");
  }

  if(sim_iter >= max_iter) {
    force.stop();
    // hack?
    // fix the node positions so that they don't
    // move (unless manually moved)
    $.each(root.nodes, function(i, d) {
      d.fixed = 1;
    });
    link.attr("x1", function(d) { return d.source.x; })
        .attr("y1", function(d) { return d.source.y; })
        .attr("x2", function(d) { return d.target.x; })
        .attr("y2", function(d) { return d.target.y; });

    node.attr("cx", function(d) { return d.x; })
        .attr("cy", function(d) { return d.y; });
    // show the chart and remove the progress
    $("#progress").hide();
    $("#chart").show();
  }
}

function addNewNode(d) {
  if(true) {
    // hack: force reset
    svg.selectAll("circle.node").data([]).exit().remove();
    svg.selectAll("line.link").data([]).exit().remove();
  }
  root.nodes.push(d);
  updateLinkView(true);
  updateNodeView(true);
  force.start();
  selectNode(d);
}

function updateNodeView() {
  node = svg.selectAll("circle.node")
    .data(root.nodes)
      .enter()
        .append("circle")
        .on("mouseover", onNodeover)
        .on("mouseout", onNodeout)
        .on("click", onNodeclick)
        .attr("class", "node")
        .attr("r", node_radius)
        .attr("id", function(d) { return "n" + d.index; })
        .style("fill", function(d) { return color(d.group); })
        .call(force.drag);

  svg.selectAll("circle.node title")
    .data(root.nodes)
    .enter()
      .append("title")
      .text(function(d) { return d.name; });
}

function updateLinkView() {
  link = svg.selectAll("line.link").data(root.links)
  link
    .enter()
      .append("line")
      .attr("class", "link")
      .style("stroke-width", function(d) { return link_weight; });
}