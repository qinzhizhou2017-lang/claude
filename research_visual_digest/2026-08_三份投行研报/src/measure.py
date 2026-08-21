#!/usr/bin/env python3
"""Report per-page content overflow for a digest HTML (headless Chromium DOM dump)."""
import subprocess, sys, re, os, tempfile
CHROME="/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
src=sys.argv[1]
html=open(src).read()
probe = """
<script>
window.addEventListener('load',function(){
 setTimeout(function(){
  var out=[];
  document.querySelectorAll('.page').forEach(function(p,i){
    var m=p.querySelector('.main');
    var avail=m.clientHeight, used=0;
    Array.from(m.children).forEach(function(c){used+=c.getBoundingClientRect().height;});
    var gaps=(m.children.length-1);
    out.push('P'+(i+1)+' avail='+Math.round(avail)+' used='+Math.round(used)+' children='+m.children.length+' slack='+Math.round(avail-used));
    Array.from(m.children).forEach(function(c,j){
      out.push('   c'+j+' '+Math.round(c.getBoundingClientRect().height)+'px  '+(c.className||c.tagName));
    });
  });
  var d=document.createElement('pre');d.id='MEASURE';d.textContent=out.join('\\n');
  document.body.appendChild(d);
 },300);
});
</script>
"""
tmp=src.replace('.html','.__probe.html')
open(tmp,'w').write(html.replace('</body>',probe+'</body>'))
r=subprocess.run([CHROME,"--headless=new","--no-sandbox","--disable-gpu","--allow-file-access-from-files",
  "--virtual-time-budget=6000","--dump-dom","file://"+os.path.abspath(tmp)],capture_output=True,text=True)
os.remove(tmp)
m=re.search(r'<pre id="MEASURE">(.*?)</pre>', r.stdout, re.S)
print(m.group(1) if m else "NO MEASUREMENT\n"+r.stderr[-800:])
