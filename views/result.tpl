% for name, content in results.iteritems():
<h1>File: {{name}} </h1>
<h2>Result</h2>
<pre>
{{content["pyang_stderr"]}}
</pre>

<h2>Output</h2>
<pre>
{{content["pyang_output"]}}
</pre>
