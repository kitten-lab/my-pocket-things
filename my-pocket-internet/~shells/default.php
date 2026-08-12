<!-- CHESTER'S NOTE: This is the default shell for the space. 
 It defines the basic structure of the HTML page, including the header, navigation, main content area, and footer. 
 The setDropSpot function is used to insert content into specific sections of the page. This is the fallback shell. -->

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

  <!-- Drop Spot for navigation and main content -->
  <div class="container">
    <nav>
      <?php setDropSpot('navigation') ?>
    </nav>
    <main>
      <?php setDropSpot('body') ?>
    </main>
  </div>

  <!-- Drop Spot for footer content -->
  <footer>
    <?php setDropSpot('footer') ?>
  </footer>

</body>
</html>

<!-- Drop Spot for javascript functions and console logs -->
<?php setDropSpot('functions') ?>
<?php setDropSpot('logs') ?>