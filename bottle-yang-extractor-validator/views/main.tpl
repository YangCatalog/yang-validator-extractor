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
                '<h3>XYM Extraction</h3><pre class="xymstderr"/>' +
                '<h3>Pyang Validation</h3><pre class="pyangstderr"/>' +
                '<h3>Pyang Output</h3><pre class="pyangoutput"/>' +
                '<h3>Confdc Output</h3><pre class="confdcstderr"/>');
            $( '#' + sanitized + ' > pre.xymstderr' ).append(data[key].xym_stderr.length > 0 ? data[key].xym_stderr : "No warnings or errors");
            $( '#' + sanitized + ' > pre.pyangstderr' ).append(data[key].pyang_stderr.length > 0 ? data[key].pyang_stderr : "No warnings or errors");
            $( '#' + sanitized + ' > pre.pyangoutput' ).append(data[key].pyang_output.length > 0 ? data[key].pyang_output : "No output");
            $( '#' + sanitized + ' > pre.confdcstderr' ).append(data[key].confdc_stderr.length > 0 ? data[key].confdc_stderr : "No warnings or errors");
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
                '<h3>XYM Extraction</h3><pre class="xymstderr"/>' +
                '<h3>Pyang Validation</h3><pre class="pyangstderr"/>' +
                '<h3>Pyang Output</h3><pre class="pyangoutput"/>' +
                '<h3>Confdc Output</h3><pre class="confdcstderr"/>');
            $( '#' + sanitized + ' > pre.xymstderr' ).append(data[key].xym_stderr.length > 0 ? data[key].xym_stderr : "No warnings or errors");
            $( '#' + sanitized + ' > pre.pyangstderr' ).append(data[key].pyang_stderr.length > 0 ? data[key].pyang_stderr : "No warnings or errors");
            $( '#' + sanitized + ' > pre.pyangoutput' ).append(data[key].pyang_output.length > 0 ? data[key].pyang_output : "No output");
            $( '#' + sanitized + ' > pre.confdcstderr' ).append(data[key].confdc_stderr.length > 0 ? data[key].confdc_stderr : "No output");          }
        });
        return(false);
      }); 
    });
  </script>
  <link href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="/static/css/pyangui.css">
  <title>YANG Extractor and Validator</title>
</head>
<body>
  <div class="container">
  <a href="https://github.com/cmoberg/bottle-yang-extractor-validator"><img style="position: absolute; top: 0; right: 0; border: 0;" src="https://camo.githubusercontent.com/a6677b08c955af8400f44c6298f40e7d19cc5b2d/68747470733a2f2f73332e616d617a6f6e6177732e636f6d2f6769746875622f726962626f6e732f666f726b6d655f72696768745f677261795f3664366436642e706e67" alt="Fork me on GitHub" data-canonical-src="https://s3.amazonaws.com/github/ribbons/forkme_right_gray_6d6d6d.png"></a>
      <ul class="nav nav-pills">
        <li role="presentation" class="active"><a href="/">Home</a></li>
        <li role="presentation"><a href="/rest">REST API</a></li>
        <li role="presentation"><a href="/about">About</a></li>
      </ul>
  <h1>Fetch, extract and validate YANG models</h1>
    <p class="lead" >The form below allows you to fetch, extract and validate YANG modules by RFC number, by IETF draft name, or by uploading IETF drafts or YANG files.</p>

        <form name="uploadform" id="uploadform" action="/validator" method="post" enctype="multipart/form-data">
          <div class="form-group">
            <label for="data" class="info">Upload multiple YANG files or a zip archive</label>
            <div class="form-inline">
              <input type="file" id="data" name="data" class="form-control" multiple="multiple" />
              <button id="file_submit" class="btn btn-default">Validate</button>
            </div>
          </div>
        </form>

        <form name="uploadid" id="uploadid" action="/draft-validator" method="post" enctype="multipart/form-data">
          <div class="form-group">
            <label for="data" class="info">Upload Internet Draft</label>
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
        % if "xym_stderr" in content:
        <h3>Extraction</h3>
        <pre class="stderr">{{!content["xym_stderr"] if len(content["xym_stderr"]) != 0 else "No warnings or errors"}}</pre>
        % end
        <h3>Validation</h3>
        <pre class="stderr">{{!content["pyang_stderr"] if len(content["pyang_stderr"]) != 0 else "No warnings or errors"}}</pre>
        <h3>Output</h3>
        <pre class="output">{{!content["pyang_output"] if len(content["pyang_output"]) != 0 else "No warnings or errors"}}</pre>
        <pre class="output">{{!content["confdc_stderr"] if len(content["confdc_stderr"]) != 0 else "No warnings or errors"}}</pre>
      </div>
    % end 
  % end
    <small class="text-muted">validator version: {{versions["validator_version"]}}, xym version: {{versions["xym_version"]}}, pyang version: {{versions["pyang_version"]}} confdc version: {{versions["confdc_version"]}}</small>
  </div>
</body>

