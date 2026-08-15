<?php
$kinds = listKinds();
if ($kinds === []) {
  echo "<p>No kinds on the host. Put papers in ~storage/~library/kinds/.</p>";
  return;
}

$meta = [];
foreach ($kinds as $type => $paper) {
  $meta[$type] = [
    'letter' => kindFlag($paper, 'letter', 'no'),
    'good' => kindFlag($paper, 'good', 'no'),
    'cite' => kindFlag($paper, 'cite', 'no'),
    'auth' => kindFlag($paper, 'auth', 'space'),
    'lines' => kindLines($paper),
  ];
}

$first = array_key_first($meta);
echo "<form method='post' enctype='multipart/form-data' id='venformer'>";
echo "<p><label for='kind'>Kind</label><br><select id='kind' name='kind'>";
foreach ($meta as $type => $spec) {
  $sel = ($type === $first) ? " selected" : '';
  echo "<option value='" . htmlspecialchars($type) . "'" . $sel . ">" . htmlspecialchars($type) . "</option>";
}
echo "</select></p>";

echo "<p data-line='title'><label for='title'>Title</label><br><input type='text' id='title' name='title'></p>";
echo "<p data-line='writer'><label for='writer'>Writer</label><br><input type='text' id='writer' name='writer'></p>";
echo "<p data-line='good'><label for='good'>Picture</label><br><input type='file' id='good' name='good' accept='image/png,image/jpeg,image/gif,image/webp'></p>";
echo "<p data-line='cite'><label for='cite'>Cite</label><br><input type='text' id='cite' name='cite' placeholder='~storage/library/goods/…'></p>";

$seen = [];
foreach ($meta as $spec) {
  foreach ($spec['lines'] as $line) {
    if (isset($seen[$line])) {
      continue;
    }
    $seen[$line] = true;
    echo "<p data-line='" . htmlspecialchars($line) . "'><label for='prop_" . htmlspecialchars($line) . "'>" . htmlspecialchars($line) . "</label><br>";
    echo "<input type='text' id='prop_" . htmlspecialchars($line) . "' name='prop_" . htmlspecialchars($line) . "'></p>";
  }
}

echo "<p data-line='letter'><label for='letter'>Letter</label><br><textarea id='letter' name='letter' rows='8'></textarea></p>";
echo "<p><input type='submit' name='venform' value='Mint'></p>";
echo "</form>";
echo "<script>\n";
echo "window.KIND_SPEC = " . json_encode($meta) . ";\n";
echo <<<'JS'
(function () {
  var spec = window.KIND_SPEC || {};
  var form = document.getElementById('venformer');
  var kind = document.getElementById('kind');
  if (!form || !kind) return;
  function shape() {
    var k = spec[kind.value] || { letter: 'yes', good: 'no', cite: 'no', auth: 'space', lines: [] };
    var keep = { title: true };
    if (k.auth === 'writer') keep.writer = true;
    if (k.good === 'yes') keep.good = true;
    if (k.cite === 'yes') keep.cite = true;
    if (k.letter === 'yes') keep.letter = true;
    (k.lines || []).forEach(function (line) { keep[line] = true; });
    if (k.letter === 'no' && k.good === 'yes') delete keep.title;
    form.querySelectorAll('[data-line]').forEach(function (row) {
      var on = !!keep[row.getAttribute('data-line')];
      row.hidden = !on;
      row.querySelectorAll('input,textarea').forEach(function (el) {
        if (el.type === 'file') return;
        el.disabled = !on;
      });
    });
  }
  kind.addEventListener('change', shape);
  shape();
})();
JS;
echo "</script>\n";
