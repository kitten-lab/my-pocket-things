<?php setDropSpot('server') ?>
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title><?= Space_Display ?> – <?= Space_Description ?></title>
    <meta name="description" content="<?= Space_Description ?>">
    <?php setDropSpot('styles') ?>
  </head>
  <body class="leak">
    <a class="skip" href="#stream">Skip to content</a>
    <nav class="leak-nav">
      <?php setDropSpot('navigation') ?>
    </nav>
    <header class="leak-mast">
      <?php setDropSpot('header') ?>
    </header>
    <main id="stream" class="leak-stream">
      <?php setDropSpot('body') ?>
    </main>
    <footer class="leak-foot">
      <?php setDropSpot('footer') ?>
    </footer>
  </body>
</html>
<?php setDropSpot('functions') ?>
<?php setDropSpot('logs') ?>
