<!-- This is a simple shell template for the common structure of the space. 
 It defines the basic structure of the HTML page, including the header, navigation, main content area, and footer. 
 The styling of the page is handled by the styles defined in the styles directory.
 The setDropSpot function is used to insert content into specific sections of the page. -->

<!-- Drop Spot for server-side scripts -->
<?php setDropSpot('server') ?>
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title><?= Space_Display ?></title>
    <meta name="description" content="<?= Space_Description ?>">

    <!-- Drop Spot for styles -->
    <?php setDropSpot('styles') ?>
</head>

<body>
  <!-- Drop Spot for header content -->
  <header>
    <?php setDropSpot('header') ?>
  </header>
  <!-- Drop Spot for navigation -->
  <nav>
    <?php setDropSpot('navigation') ?>
  </nav>
  <!-- Drop Spot for main content -->
  <main>
    <?php setDropSpot('body') ?>
  </main>
  <!-- Drop Spot for footer content -->
  <footer>
    <?php setDropSpot('footer') ?>
  </footer>
</body>
</html>

<!-- Drop Spot for javascript functions and console logs -->
<?php setDropSpot('functions') ?>
<?php setDropSpot('logs') ?>