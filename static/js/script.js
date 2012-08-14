/* Author: Aaron Perrin

*/

function addNewObject(obj_type) {
  $('#modal_insert').load('/api/modeltemplates/' + obj_type + '.html', function() {
    $('#modal').modal();
    // put it in a random posiiton in the top left portion of the view
    x1 = 10 + w * .2 * Math.random();
    y1 = 10 + w * .2 * Math.random();
    newObj = {x: x1, y: y1, group:9, index: force.nodes().length};
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

var w = 1000,
    h = 600;

var svg = d3.select("#chart")
  .append("svg")
  //.on("click", onClickCanvas)
  .attr("width", w)
  .attr("height", h);

var force;
var link;
var node;
var root;

var node_radius = 5;
var sim_iter = 0;
var max_iter = 0;
var base_grav = 0.09;
var link_dist = 20;
var charge = -18;
var grav = 0;
var link_weight = 2;
var _selected_table;

var color = d3.scale.category10();

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
  force.start();

  addLinks(json.links);
  addNodes(json.nodes);

  force.on("tick", onTick);
});

function onClickCanvas() {
  point = d3.mouse(this);
  addNewNode({name:"new",type:"new",group:0,x:point[0],y:point[1],fixed:1});
}

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
        //addNodes(force.nodes());
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
  force.nodes().push(d);
  // todo: add links, probably not here
  //last_n = force.nodes().length-1;
  //force.links().push({source:last_n,target:last_n-1,value:link_weight});
  //addLinks(force.links());
  addNodes(force.nodes());
  force.start();
  selectNode(d);
}

function addNodes(data) {
  data = svg.selectAll("circle.node").data(data)
  node = data.enter()
      .append("circle")
      .on("mouseover", onNodeover)
      .on("mouseout", onNodeout)
      .on("click", onNodeclick)
      .attr("class", "node")
      .attr("cx", function(d) { return w/2; })
      .attr("cy", function(d) { return h/2; })
      .attr("r", node_radius)
      .attr("id", function(d) { return "n" + d.index; })
      .style("fill", function(d) { return color(d.group); })
      .call(force.drag);

  node.append("title")
    .text(function(d) { return d.name; });

  data
    .exit()
      .remove();
}

function addLinks(data) {
  link = svg.selectAll("line.link").data(data)
  link
    .enter()
      .append("line")
      .attr("class", "link")
      .style("stroke-width", function(d) { return link_weight; });
  link
    .exit()
      .remove();
}