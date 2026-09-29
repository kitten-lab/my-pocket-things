---
crate: crate.F9F09722D4843565
title: pet.sums
---

# pet sums

```
1   000   001   002 |   003
2   010   011   012 |   033
3   020   021   022 |   063
4   030   031   032 |   093
5   100   101   102    303
```

counting is a linear layer system
where each higher layer is 

COMPARISON CHARTS
COMPARE AGAINST BASE10 count

```
nums#  
--- --1  --2  --3  --4  --5  --6  --7  --8  --9   --1-  --11  --12  BASE10
--- --1  --1  --2  --3  --5  --8  -13  -21  -34   --55  --89  -144  FIB
--- --3  --6  --9  -12  -15  -18  -21  -24  -27   --3-  --33  --36  STEP3
--- -12  -24  -36  -48  -6-  -72  -84  -96  1-8   -12-  -132  -144  STEP12
--- --2  --4  --6  --8  -1-  -12  -14  -16  -18   --2-  --22  --24  STEP2
--- --2  --4  --8  -16  -32  -64  128  256  512   1-24  2-48  4-96  POWERS2
```


each - represents nothing
```
SOMETHING (represented as [[an about]] of it)
.

NOTHING


```

## moire
```
(next number in base 10 count)[total sum of sequence]{representative layer}

		           STEP3          >B10   MOD9      LAYER   BOX-MOD9
--------|-----------------------------------------------------------
    	|	 ---- ---3 ---6 ---9   (4)   [5]       {ones}   0 3 6 9
  B10 	|	 --12 --15 --18 --21   (8)   [37/10/1] {tens}   3 6 9 3
  POS 	| 	 --24 --27 --30 --33   (12)  [96/12/3] {tens}   6 9 3 6
 (BY	|    --36 --39 --42 --45   (16)  [162/9]   {tens}   9 3 6 9
LAYER)	|    --48 --51 --54 --57                   {huns}
		|    --59 --
```
