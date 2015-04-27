<!DOCTYPE html>
<html lang="en">
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <script src="https://ajax.googleapis.com/ajax/libs/jquery/2.1.3/jquery.min.js"></script>
  <script type="text/javascript">
    $( document ).ready(function() {
      var rfc_number = 0;
      var draft_name = "";

      $( "#rfc_submit" ).click(function() {
        rfc_number = $( "#rfc_number" ).val();
        $.ajax({
            url: "/api/rfc/" + rfc_number,
        }).then(function(data, textStatus, jqXHR) {
          $( "#maincanvas" ).empty()
          $( '#maincanvas' ).append('<hr>');
          $( '#maincanvas' ).append('<p>Extracted ' + Object.keys(data).length + ' YANG module(s)</p>');          
          $( '#maincanvas' ).append('<ul>');
          for (var key in data) {
            sanitized = key.split("@")[0].replace(".", "_");
            $( '#maincanvas' ).append('<li><a href="#' + sanitized + '">' + key + '</a></li>');
          }
          $( '#maincanvas' ).append('</ul>');
          for (var key in data) {
            $( '#maincanvas' ).append('<hr>');
            sanitized = key.split("@")[0].replace(".", "_");
            $( '#maincanvas' ).append('<div id="' + sanitized + '"> <h2>' + key + '</h2>' +
                '<h3>Extraction</h3><pre class="xymstderr"/>' +
                '<h3>Validation</h3><pre class="stderr"/>' +
                '<h3>Output</h3><pre class="output"/>');
            $( '#' + sanitized + ' > pre.xymstderr' ).append(data[key].xym_stderr);
            $( '#' + sanitized + ' > pre.stderr' ).append(data[key].pyang_stderr);
            $( '#' + sanitized + ' > pre.output' ).append(data[key].pyang_output);
          }
        });
        return(false);
      });

      $( "#draft_submit" ).click(function() {
        draft_name = $( "#draft_name" ).val();
        $.ajax({
            url: "/api/draft/" + draft_name,
        }).then(function(data, textStatus, jqXHR) {
          $( "#maincanvas" ).empty()
          $( '#maincanvas' ).append('<hr>');
          $( '#maincanvas' ).append('<p>Extracted ' + Object.keys(data).length + ' YANG module(s)</p>');          
          $( '#maincanvas' ).append('<ul>');
          for (var key in data) {
            sanitized = key.split("@")[0].replace(".", "_");
            $( '#maincanvas' ).append('<li><a href="#' + sanitized + '">' + key + '</a></li>');
          }
          $( '#maincanvas' ).append('</ul>');
          for (var key in data) {
            $( '#maincanvas' ).append('<hr>');
            sanitized = key.split("@")[0].replace(".", "_");
            $( '#maincanvas' ).append('<div id="' + sanitized + '"> <h2>' + key + '</h2>' +
                '<h3>Extraction</h3><pre class="xymstderr"/>' +
                '<h3>Validation</h3><pre class="stderr"/>' +
                '<h3>Output</h3><pre class="output"/>');
            $( '#' + sanitized + ' > pre.xymstderr' ).append(data[key].xym_stderr);
            $( '#' + sanitized + ' > pre.stderr' ).append(data[key].pyang_stderr);
            $( '#' + sanitized + ' > pre.output' ).append(data[key].pyang_output);
          }
        });
        return(false);
      }); 
    });
  </script>
  <link href="//maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="/static/css/pyangui.css">
  <title>YANG Extractor and Validator</title>
</head>
<body>
<div class="container">
<h1>Fetch, extract and validate YANG models</h1>
  <p class="lead" >The form below allows you to fetch, extract and validate YANG modules by RFC number, by IETF draft name, or by uploading YANG files. It is built using a combination of <a href="https://github.com/YangModels/yang/tree/master/tools/xym">xym</a> to fetch and extract YANG modules from IETF specifications, and <a href="https://github.com/mbj4668/pyang">pyang</a> to validate the extracted modules.</p>

      <form name="uploadform" id="uploadform" action="/validator" method="post" enctype="multipart/form-data">
        <div class="form-group">
          <label for="data" class="info">Upload multiple YANG files or a zip archive</label>
          <div class="form-inline">
            <input type="file" id="data" name="data" class="form-control" multiple="multiple" />
            <button id="file_submit" class="btn btn-default">Validate</button>
          </div>
        </div>
      </form>

      <form name="rfcform" id="rfcform">
        <div class="form-group">
          <label for="rfc_number" class="info" >Fetch and validate IETF RFC by number</label>
          <div class="form-inline">
            <input  id="rfc_number" type="text" class="form-control" placeholder="RFC number, e.g. 7223" />
            <button id="rfc_submit" class="btn btn-default">Validate</button>
          </div>
        </div>
      </form>

      <form name="draftform" id="draftform">
        <div class="form-group">
          <label for="draft_name" class="info">Fetch and validate IETF Draft by name</label>
          <div class="form-inline">
            <input  id="draft_name" type="text" class="form-control" placeholder="Draft name, e.g. draft-ietf-netmod-syslog-model" />
            <button id="draft_submit" class="btn btn-default">Validate</button>
          </div>
        </div>
      </form>

  <div id="maincanvas" />
    <hr>
% if len(results) != 0:
    <p>Extracted {{len(results)}} YANG modules</p>
    <ul>
  % for name, content in results.iteritems():
      <li><a href="#{{name.split("@")[0].replace(".", "_")}}">{{name}}</a></li>
  % end
    </ul>
%end

% if len(results) != 0:
  % for name, content in results.iteritems():
    <div>
      <hr>
      <h2 id="{{name.split("@")[0].replace(".", "_")}}">{{name}}</h2>
      <h3>Validation</h3>
      <pre class="stderr">{{content["pyang_stderr"]}}</pre>
      <h3>Output</h3>
      <pre class="output">{{content["pyang_output"]}}</pre>
    </div>
  % end 
% end
</div>
</body>

