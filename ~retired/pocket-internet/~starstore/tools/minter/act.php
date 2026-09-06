<?php
if (!function_exists('mintUploadedGood')) {
    function mintUploadedGood(?string $asType = null): ?array {
        if (empty($_FILES['good']) || !is_array($_FILES['good'])) {
            return null;
        }
        $upload = $_FILES['good'];
        if (($upload['error'] ?? UPLOAD_ERR_NO_FILE) !== UPLOAD_ERR_OK) {
            return null;
        }
        $allowed = [
            'jpg' => 'image/jpeg',
            'jpeg' => 'image/jpeg',
            'png' => 'image/png',
            'gif' => 'image/gif',
            'webp' => 'image/webp',
        ];
        $ext = strtolower(pathinfo((string) $upload['name'], PATHINFO_EXTENSION));
        if (!isset($allowed[$ext])) {
            loadContent('body', '<div class="alert-error">That is not a good we keep (png, jpg, gif, webp).</div>');
            return null;
        }
        $tmp = (string) $upload['tmp_name'];
        $info = @getimagesize($tmp);
        if ($info === false || !in_array($info['mime'], $allowed, true)) {
            loadContent('body', '<div class="alert-error">That file is not an image we can mint.</div>');
            return null;
        }

        $fileKind = openKind('GOODS');
        $type = $asType ?: ($fileKind ? (string) chipAsk($fileKind, 'kind.type') : 'GOODS');
        $mint = mintChipName($type);
        $stem = Space_Code . '-' . $mint['type'] . '-' . $mint['code'] . '.' . $ext;
        if (!writeGoodBoth($stem, $tmp)) {
            loadContent('body', '<div class="alert-error">Could not dual-write the good.</div>');
            return null;
        }

        $title = wirePostInput('title');
        if ($title === '') {
            $title = (string) $upload['name'];
        }
        $filePointer = masterGoodPointer($stem);
        $paper = chipHead([
            'library' => [
                'file' => $mint['pointer'],
                'type' => 'chip',
                'class' => strtolower($mint['type']),
            ],
            'chip' => [
                'cuid' => $mint['cuid'],
                'auth' => Space_Slug,
                'title' => $title,
            ],
            'origin' => [
                'space' => Space_Slug,
                'type' => strtolower($mint['type']),
                'tool' => 'minter',
            ],
            'notch' => [
                'mint' => date('Y-m-d H:i:s'),
                'tags' => '[' . strtolower($mint['type']) . ']',
                'cites' => '[' . $filePointer . ']',
                'owners' => '[' . Space_Slug . ']',
            ],
        ], '');
        writeChipBoth($mint['filename'], $paper);

        return [
            'chip' => $mint['pointer'],
            'file' => $filePointer,
            'filename' => $mint['filename'],
            'type' => $mint['type'],
        ];
    }
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST' || !isset($_POST['venform'])) {
    return;
}

$kindName = strtoupper(preg_replace('/[^a-z]/i', '', wirePostInput('kind')));
$kind = openKind($kindName);
if ($kind === null) {
    loadContent('body', '<div class="alert-error">No kind paper for ' . htmlspecialchars($kindName) . '.</div>');
    return;
}

$wantsLetter = kindFlag($kind, 'letter', 'no') === 'yes';
$wantsGood = kindFlag($kind, 'good', 'no') === 'yes';
$wantsCite = kindFlag($kind, 'cite', 'no') === 'yes';
$authMode = kindFlag($kind, 'auth', 'space');
$lines = kindLines($kind);
$fileOnly = !$wantsLetter && $wantsGood;

$cite = $wantsCite ? normalizeGoodCite(wirePostInput('cite')) : '';
$uploaded = $wantsGood ? mintUploadedGood() : null;
if ($uploaded !== null) {
    $cite = $uploaded['file'];
    if ($fileOnly) {
        loadContent('body', '<div class="alert-success">Minted ' . htmlspecialchars($uploaded['type']) . ' <code>' . htmlspecialchars($uploaded['chip']) . '</code></div>');
        return;
    }
}

if ($fileOnly) {
    loadContent('body', '<div class="alert-error">This kind needs a picture.</div>');
    return;
}

$title = wirePostInput('title');
$letter = $wantsLetter ? (isset($_POST['letter']) ? trim((string) $_POST['letter']) : '') : '';
$writer = wirePostInput('writer');

if ($wantsLetter && ($title === '' || $letter === '')) {
    loadContent('body', '<div class="alert-error">This kind needs a title and a letter.</div>');
    return;
}
if ($authMode === 'writer' && $writer === '') {
    loadContent('body', '<div class="alert-error">This kind needs a writer. The space owns the chip.</div>');
    return;
}

$props = [];
foreach ($lines as $line) {
    $props[$line] = wirePostInput('prop_' . $line);
}

$type = (string) chipAsk($kind, 'kind.type');
$mint = mintChipName($type);
$class = strtolower($mint['type']);
$auth = ($authMode === 'writer') ? $writer : Space_Slug;

$tree = [
    'library' => [
        'file' => $mint['pointer'],
        'type' => 'chip',
        'class' => $class,
    ],
    'chip' => [
        'cuid' => $mint['cuid'],
        'auth' => $auth,
        'title' => $title !== '' ? $title : $mint['cuid'],
    ],
    'origin' => [
        'space' => Space_Slug,
        'type' => $class,
        'tool' => 'minter',
    ],
    'notch' => [
        'mint' => date('Y-m-d H:i:s'),
        'tags' => '[' . $class . ']',
        'cites' => $cite === '' ? '[]' : '[' . $cite . ']',
        'owners' => '[' . Space_Slug . ']',
    ],
];
if ($props !== []) {
    $tree['prop'] = $props;
}

writeChipBoth($mint['filename'], chipHead($tree, $letter));
loadContent('body', '<div class="alert-success">Minted ' . htmlspecialchars($mint['type']) . ' <code>' . htmlspecialchars($mint['pointer']) . '</code></div>');
