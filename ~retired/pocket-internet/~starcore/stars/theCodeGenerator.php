<?php
/** CHESTER'S NOTE: The Code Generator can help you generate random codes */
      
function generateRandomCode($totalLength = 6) {
    // Ensure the length is even so it can be split exactly 50/50
    if ($totalLength % 2 !== 0) {
        $totalLength++;
    }

    $halfLength = $totalLength / 2;
    $lettersPool = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    $numbersPool = '0123456789';
    
    $chosenCharacters = [];

    // 1. Pick secure random letters
    for ($i = 0; $i < $halfLength; $i++) {
        $randomIndex = random_int(0, strlen($lettersPool) - 1);
        $chosenCharacters[] = $lettersPool[$randomIndex];
    }

    // 2. Pick secure random numbers
    for ($i = 0; $i < $halfLength; $i++) {
        $randomIndex = random_int(0, strlen($numbersPool) - 1);
        $chosenCharacters[] = $numbersPool[$randomIndex];
    }

    // 3. Split into two equal parts and insert the dash
    $firstHalf = array_slice($chosenCharacters, 0, $halfLength);
    $secondHalf = array_slice($chosenCharacters, $halfLength);

    return implode('', $firstHalf) . '_' . implode('', $secondHalf);
}

/** One name law: Space_Code-TYPE-chipcode.chip. TYPE comes from a kind paper. */
function mintChipName(string $type): array {
    $type = strtoupper(preg_replace('/[^a-z]/i', '', $type));
    if (strlen($type) < 2 || strlen($type) > 16) {
        $type = 'CHIP';
    }
    $code = generateRandomCode();
    $filename = Space_Code . '-' . $type . '-' . $code . '.chip';
    return [
        'type' => $type,
        'code' => $code,
        'filename' => $filename,
        'cuid' => $type . '-' . $code,
        'pointer' => masterChipPointer($filename),
    ];
}