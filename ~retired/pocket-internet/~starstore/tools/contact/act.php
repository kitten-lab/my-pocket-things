<?php
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['message']) && !isset($_POST['venform'])) {
    $name = wirePostInput('name');
    $space = wirePostInput('space');
    $message = wirePostInput('message');
    if ($name === '' || $space === '' || $message === '') {
        return;
    }

    $mint = mintChipName('MSG');
    $body = chipHead([
        'library' => [
            'file' => $mint['pointer'],
            'type' => 'chip',
            'class' => 'message',
        ],
        'chip' => [
            'cuid' => $mint['cuid'],
            'auth' => Space_Author,
            'title' => 'Message from ' . $name,
        ],
        'origin' => [
            'space' => Space_Slug,
            'type' => 'contact',
            'tool' => 'contact',
        ],
        'contact' => [
            'to' => Space_Author,
            'to_space' => Space_Slug,
            'from' => $name,
            'from_space' => $space,
        ],
        'notch' => [
            'mint' => date('Y-m-d H:i:s'),
            'tags' => '[contact, message]',
            'cites' => '[]',
            'owners' => '[' . Space_Slug . ']',
        ],
    ], $message);
    writeChipBoth($mint['filename'], $body);

    loadContent('body', '<div class="alert-success">Thank you for your message, ' . htmlspecialchars($name) . '! We will get back to you at ' . htmlspecialchars($space) . '</div>');
}
