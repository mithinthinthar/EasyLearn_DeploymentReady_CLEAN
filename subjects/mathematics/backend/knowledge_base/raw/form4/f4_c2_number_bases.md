# Topic: Number Bases
**Form:** Form 4 | **Chapter:** Chapter 2 | **Curriculum:** SPM KSSM

## Overview
Number bases are number systems that use a fixed set of digits to represent values. In this topic, students learn how to identify valid digits in different bases, determine place values and digit values, convert numbers between bases, and perform addition and subtraction in various bases.

## Concept: Number Bases and Digits
A number base is a number system made up of digits. Each base uses digits starting from $0$ up to one digit less than the base.

**Key Rules / Methods:**
- Base ten is also called the decimal number system.
- Digits are symbols used to form numbers.
- The ten digits used in the decimal number system are $0, 1, 2, 3, 4, 5, 6, 7, 8, 9$.
- In base $a$, the largest digit allowed is $a - 1$.
- A number written in a certain base is shown using a subscript, such as $325_5$.
- $325_5$ is read as “three two base five”.

Digits used in bases from base $2$ to base $10$:
- Base $2$: $0, 1$
- Base $3$: $0, 1, 2$
- Base $4$: $0, 1, 2, 3$
- Base $5$: $0, 1, 2, 3, 4$
- Base $6$: $0, 1, 2, 3, 4, 5$
- Base $7$: $0, 1, 2, 3, 4, 5, 6$
- Base $8$: $0, 1, 2, 3, 4, 5, 6, 7$
- Base $9$: $0, 1, 2, 3, 4, 5, 6, 7, 8$
- Base $10$: $0, 1, 2, 3, 4, 5, 6, 7, 8, 9$

### Worked Example:
Give two examples of numbers that represent numbers in base $2$ up to base $10$.

| Number Base | Example Numbers |
|---|---|
| Base $2$ | $10_2$, $1001_2$ |
| Base $3$ | $21_3$, $1201_3$ |
| Base $4$ | $23_4$, $213_4$ |
| Base $5$ | $41_5$, $342_5$ |
| Base $6$ | $35_6$, $4510_6$ |
| Base $7$ | $64_7$, $463_7$ |
| Base $8$ | $17_8$, $472_8$ |
| Base $9$ | $78_9$, $385_9$ |
| Base $10$ | $69_{10}$, $2893_{10}$ |

### Common Mistakes & Exam Tips:
- A digit in a number must be smaller than the base.
- $217_7$ is not valid because the digit $7$ cannot appear in base $7$.
- $829_9$ is not valid because the digit $9$ cannot appear in base $9$.
- Always check the digits before doing conversion or calculation.

## Concept: Place Values in Number Bases
Each number base has place values according to repeated powers of that base.

**Key Rules / Methods:**
- If the base is $a$, the place values are powers of $a$:

$$
a^0, a^1, a^2, a^3, \ldots, a^n
$$

- From right to left, the place values increase by powers of the base.
- The rightmost digit always has place value $a^0 = 1$.
- For base $2$, the place values are $2^0, 2^1, 2^2, 2^3, \ldots$.
- For base $8$, the place values are $8^0, 8^1, 8^2, 8^3, \ldots$.

### Worked Example:
State the place value of each digit in $6231_8$.

| Digit | $6$ | $2$ | $3$ | $1$ |
|---|---:|---:|---:|---:|
| Place Value | $8^3$ | $8^2$ | $8^1$ | $8^0$ |

State the place value of each digit in $111101_2$.

| Digit | $1$ | $1$ | $1$ | $1$ | $0$ | $1$ |
|---|---:|---:|---:|---:|---:|---:|
| Place Value | $2^5$ | $2^4$ | $2^3$ | $2^2$ | $2^1$ | $2^0$ |

### Common Mistakes & Exam Tips:
- Start assigning place values from the rightmost digit.
- Do not start from the left unless the number of digits is already known.
- Remember that the rightmost place value is always $a^0$.

## Concept: Digit Value in Various Bases
The value of a particular digit in a number is obtained by multiplying the digit by its place value.

**Key Rules / Methods:**
- Digit value is calculated as:

$$
\text{Digit value} = \text{Digit} \times \text{Place value}
$$

- The place value depends on the base and position of the digit.
- A digit may look the same in different bases, but its value can be different because the place value changes.

### Worked Example:
State the value of the underlined digit in $271_8$, where the underlined digit is $2$.

The digit $2$ is in the $8^2$ place.

$$
2 \times 8^2 = 2 \times 64
$$

$$
= 128
$$

Therefore, the value of the digit $2$ is $128$.

### Worked Example:
State the value of the underlined digit in $5037_9$, where the underlined digit is $5$.

The digit $5$ is in the $9^3$ place.

$$
5 \times 9^3 = 5 \times 729
$$

$$
= 3645
$$

Therefore, the value of the digit $5$ is $3645$.

### Worked Example:
State the value of the underlined digit in $3501_6$, where the underlined digit is $5$.

The digit $5$ is in the $6^2$ place.

$$
5 \times 6^2 = 5 \times 36
$$

$$
= 180
$$

Therefore, the value of the digit $5$ is $180$.

### Common Mistakes & Exam Tips:
- Do not treat the digit value as the digit alone.
- The same digit can have different values depending on its position and base.
- Always identify the correct place value before multiplying.

## Concept: Number Value in Various Bases
The number value of a number in a certain base is found by adding all digit values.

**Key Rules / Methods:**
- To find the value of a number in base ten:
  - Write the place value of each digit.
  - Multiply each digit by its place value.
  - Add all the digit values.
- The number value is calculated as:

$$
(d_n \times a^n) + (d_{n-1} \times a^{n-1}) + \cdots + (d_1 \times a^1) + (d_0 \times a^0)
$$

where $a$ is the base.

### Worked Example:
Determine the value of $11001_2$.

| Digit | $1$ | $1$ | $0$ | $0$ | $1$ |
|---|---:|---:|---:|---:|---:|
| Place Value | $2^4$ | $2^3$ | $2^2$ | $2^1$ | $2^0$ |
| Digit Value | $1 \times 2^4$ | $1 \times 2^3$ | $0 \times 2^2$ | $0 \times 2^1$ | $1 \times 2^0$ |

$$
11001_2 = 16 + 8 + 0 + 0 + 1
$$

$$
= 25_{10}
$$

### Worked Example:
Determine the value of $12021_3$.

| Digit | $1$ | $2$ | $0$ | $2$ | $1$ |
|---|---:|---:|---:|---:|---:|
| Place Value | $3^4$ | $3^3$ | $3^2$ | $3^1$ | $3^0$ |
| Digit Value | $1 \times 3^4$ | $2 \times 3^3$ | $0 \times 3^2$ | $2 \times 3^1$ | $1 \times 3^0$ |

$$
12021_3 = 81 + 54 + 0 + 6 + 1
$$

$$
= 142_{10}
$$

### Worked Example:
Determine the value of $3021_4$.

| Digit | $3$ | $0$ | $2$ | $1$ |
|---|---:|---:|---:|---:|
| Place Value | $4^3$ | $4^2$ | $4^1$ | $4^0$ |
| Digit Value | $3 \times 4^3$ | $0 \times 4^2$ | $2 \times 4^1$ | $1 \times 4^0$ |

$$
3021_4 = 192 + 0 + 8 + 1
$$

$$
= 201_{10}
$$

### Worked Example:
Determine the value of $1506_8$.

| Digit | $1$ | $5$ | $0$ | $6$ |
|---|---:|---:|---:|---:|
| Place Value | $8^3$ | $8^2$ | $8^1$ | $8^0$ |

$$
1506_8 = (1 \times 8^3) + (5 \times 8^2) + (0 \times 8^1) + (6 \times 8^0)
$$

$$
= 512 + 320 + 0 + 6
$$

$$
= 838_{10}
$$

### Common Mistakes & Exam Tips:
- Writing the base sign for a number in base $10$ is optional.
- Do not compare two numbers from different bases by looking only at their digits.
- Convert numbers to base $10$ first when comparing values from different bases.

## Concept: Converting Base Ten to Another Base
A number in base ten can be converted to another base using division by the target base or division using place values.

**Key Rules / Methods:**
- To convert a base ten number to another base using repeated division:
  - Divide the base ten number by the target base.
  - Record the remainder.
  - Continue dividing the quotient until the quotient becomes $0$.
  - Read the remainders from bottom to top.
- The remainders become the digits in the new base.

### Worked Example:
Convert $563_{10}$ to a number in base $5$.

Repeated division by $5$:

$$
563 \div 5 = 112 \text{ remainder } 3
$$

$$
112 \div 5 = 22 \text{ remainder } 2
$$

$$
22 \div 5 = 4 \text{ remainder } 2
$$

$$
4 \div 5 = 0 \text{ remainder } 4
$$

Read the remainders from bottom to top:

$$
563_{10} = 4223_5
$$

### Worked Example:
Convert $563_{10}$ to a number in base $8$.

Repeated division by $8$:

$$
563 \div 8 = 70 \text{ remainder } 3
$$

$$
70 \div 8 = 8 \text{ remainder } 6
$$

$$
8 \div 8 = 1 \text{ remainder } 0
$$

$$
1 \div 8 = 0 \text{ remainder } 1
$$

Read the remainders from bottom to top:

$$
563_{10} = 1063_8
$$

### Common Mistakes & Exam Tips:
- Read the remainders from bottom upwards.
- Do not read the remainders in the order they are obtained.
- Continue division until the quotient becomes $0$.

## Concept: Converting a Number from One Base to Another Base
A number in base $p$ can be converted to base $q$ by first converting it to base $10$, then converting the base $10$ value to base $q$.

**Key Rules / Methods:**
- Step $1$: Convert the number from base $p$ to base $10$ using place values.
- Step $2$: Convert the base $10$ value to base $q$ using repeated division.

$$
\text{Base } p \rightarrow \text{Base } 10 \rightarrow \text{Base } q
$$

### Worked Example:
Convert $253_6$ to a number in base $9$.

Step $1$: Convert $253_6$ to base $10$.

$$
253_6 = (2 \times 6^2) + (5 \times 6^1) + (3 \times 6^0)
$$

$$
= 72 + 30 + 3
$$

$$
= 105_{10}
$$

Step $2$: Convert $105_{10}$ to base $9$.

$$
105 \div 9 = 11 \text{ remainder } 6
$$

$$
11 \div 9 = 1 \text{ remainder } 2
$$

$$
1 \div 9 = 0 \text{ remainder } 1
$$

Read the remainders from bottom to top:

$$
105_{10} = 126_9
$$

Therefore:

$$
253_6 = 126_9
$$

### Worked Example:
Convert $334_5$ to a number in base $2$.

Step $1$: Convert $334_5$ to base $10$.

$$
334_5 = (3 \times 5^2) + (3 \times 5^1) + (4 \times 5^0)
$$

$$
= 75 + 15 + 4
$$

$$
= 94_{10}
$$

Step $2$: Convert $94_{10}$ to base $2$.

$$
94 \div 2 = 47 \text{ remainder } 0
$$

$$
47 \div 2 = 23 \text{ remainder } 1
$$

$$
23 \div 2 = 11 \text{ remainder } 1
$$

$$
11 \div 2 = 5 \text{ remainder } 1
$$

$$
5 \div 2 = 2 \text{ remainder } 1
$$

$$
2 \div 2 = 1 \text{ remainder } 0
$$

$$
1 \div 2 = 0 \text{ remainder } 1
$$

Read the remainders from bottom to top:

$$
94_{10} = 1011110_2
$$

Therefore:

$$
334_5 = 1011110_2
$$

### Common Mistakes & Exam Tips:
- Do not convert directly between unrelated bases unless a special shortcut is given.
- Use base $10$ as the middle step for most conversions.
- Check that every digit in the final answer is allowed in the new base.

## Concept: Converting Base Two to Base Eight
A number in base $2$ can be converted directly to base $8$ because each base $8$ digit is equivalent to three base $2$ digits.

**Key Rules / Methods:**
- Separate the base $2$ number into groups of three digits from right to left.
- If the leftmost group has fewer than three digits, add leading zeros if needed.
- Find the value of each group.
- Combine the results to form the number in base $8$.

Base $2$ to base $8$ equivalences:
- $000_2 = 0_8$
- $001_2 = 1_8$
- $010_2 = 2_8$
- $011_2 = 3_8$
- $100_2 = 4_8$
- $101_2 = 5_8$
- $110_2 = 6_8$
- $111_2 = 7_8$

### Worked Example:
Convert $110111_2$ to base $8$.

Separate into groups of three digits:

$$
110\quad 111
$$

Convert each group:

$$
110_2 = 4 + 2 + 0 = 6_8
$$

$$
111_2 = 4 + 2 + 1 = 7_8
$$

Therefore:

$$
110111_2 = 67_8
$$

### Worked Example:
Convert $1101101_2$ to base $8$.

Separate into groups of three digits from right to left:

$$
1\quad 101\quad 101
$$

Add leading zeros to the first group:

$$
001\quad 101\quad 101
$$

Convert each group:

$$
001_2 = 1_8
$$

$$
101_2 = 5_8
$$

$$
101_2 = 5_8
$$

Therefore:

$$
1101101_2 = 155_8
$$

### Common Mistakes & Exam Tips:
- Group base $2$ digits from right to left, not left to right.
- Each group must contain exactly three digits.
- Add leading zeros only on the left, never at the right.

## Concept: Converting Base Eight to Base Two
A number in base $8$ can be converted directly to base $2$ because each base $8$ digit is equivalent to three base $2$ digits.

**Key Rules / Methods:**
- Separate the digits in the base $8$ number.
- Convert each digit to a three-digit base $2$ group.
- Combine all the groups to form the base $2$ number.

Base $8$ to base $2$ equivalences:
- $0_8 = 000_2$
- $1_8 = 001_2$
- $2_8 = 010_2$
- $3_8 = 011_2$
- $4_8 = 100_2$
- $5_8 = 101_2$
- $6_8 = 110_2$
- $7_8 = 111_2$

### Worked Example:
Convert $517_8$ to base $2$.

Convert each digit:

$$
5_8 = 101_2
$$

$$
1_8 = 001_2
$$

$$
7_8 = 111_2
$$

Combine the groups:

$$
517_8 = 101001111_2
$$

### Worked Example:
Convert $725_8$ to base $2$.

Convert each digit:

$$
7_8 = 111_2
$$

$$
2_8 = 010_2
$$

$$
5_8 = 101_2
$$

Combine the groups:

$$
725_8 = 111010101_2
$$

### Common Mistakes & Exam Tips:
- Each base $8$ digit must become a three-digit base $2$ group.
- Do not drop zeros in the middle groups.
- Keep leading zeros inside each three-digit group except when simplifying the final leftmost group if appropriate.

## Concept: Addition in Various Bases
Addition in number bases can be done using vertical form or by converting to base $10$.

**Key Rules / Methods:**
- Method $1$: Vertical form
  - Add digits from right to left.
  - If the sum is equal to or greater than the base, convert the sum into the given base.
  - Write the digit in the answer space and carry the next digit to the next column.
- Method $2$: Conversion of base
  - Convert each number to base $10$.
  - Add the base $10$ values.
  - Convert the answer back to the required base.

### Worked Example:
Calculate $110_2 + 111_2$.

Using conversion of base:

$$
110_2 = 6_{10}
$$

$$
111_2 = 7_{10}
$$

$$
6 + 7 = 13_{10}
$$

Convert $13_{10}$ to base $2$:

$$
13_{10} = 1101_2
$$

Therefore:

$$
110_2 + 111_2 = 1101_2
$$

Using vertical form:

$$
0 + 1 = 1_2
$$

$$
1 + 1 = 2_{10} = 10_2
$$

Write $0$ and carry $1$.

$$
1 + 1 + 1 = 3_{10} = 11_2
$$

Therefore:

$$
110_2 + 111_2 = 1101_2
$$

### Worked Example:
Calculate $673_8 + 175_8$.

Using conversion of base:

$$
673_8 = 443_{10}
$$

$$
175_8 = 125_{10}
$$

$$
443 + 125 = 568_{10}
$$

Convert $568_{10}$ to base $8$:

$$
568_{10} = 1070_8
$$

Therefore:

$$
673_8 + 175_8 = 1070_8
$$

Using vertical form:

$$
3 + 5 = 8_{10} = 10_8
$$

Write $0$ and carry $1$.

$$
1 + 7 + 7 = 15_{10} = 17_8
$$

Write $7$ and carry $1$.

$$
1 + 6 + 1 = 8_{10} = 10_8
$$

Therefore:

$$
673_8 + 175_8 = 1070_8
$$

### Worked Example:
Calculate $1837_9 + 765_9$.

Using conversion of base:

$$
1837_9 = 1411_{10}
$$

$$
765_9 = 626_{10}
$$

$$
1411 + 626 = 2037_{10}
$$

Convert $2037_{10}$ to base $9$:

$$
2037_{10} = 2713_9
$$

Therefore:

$$
1837_9 + 765_9 = 2713_9
$$

### Common Mistakes & Exam Tips:
- In vertical form, carry according to the base, not base $10$.
- The answer digits must be less than the base.
- If unsure, use conversion to base $10$ to check the answer.

## Concept: Subtraction in Various Bases
Subtraction in number bases can be done using vertical form or by converting to base $10$.

**Key Rules / Methods:**
- Method $1$: Vertical form
  - Subtract digits from right to left.
  - If the top digit is smaller than the bottom digit, borrow from the next place value.
  - When borrowing, add the base value to the digit being subtracted from.
  - The difference written must be less than the base.
- Method $2$: Conversion of base
  - Convert each number to base $10$.
  - Subtract the base $10$ values.
  - Convert the answer back to the required base.

### Worked Example:
Calculate $4005_6 - 325_6$.

Using conversion of base:

$$
4005_6 = 869_{10}
$$

$$
325_6 = 125_{10}
$$

$$
869 - 125 = 744_{10}
$$

Convert $744_{10}$ to base $6$:

$$
744_{10} = 3240_6
$$

Therefore:

$$
4005_6 - 325_6 = 3240_6
$$

Using vertical form:
- Borrow according to base $6$.
- Use $6$ when borrowing.

$$
5 - 5 = 0_6
$$

$$
6 - 2 = 4_6
$$

$$
5 - 3 = 2_6
$$

Therefore:

$$
4005_6 - 325_6 = 3240_6
$$

### Worked Example:
Calculate $6241_7 - 613_7$.

Using conversion of base:

$$
6241_7 = 2185_{10}
$$

$$
613_7 = 304_{10}
$$

$$
2185 - 304 = 1881_{10}
$$

Convert $1881_{10}$ to base $7$:

$$
1881_{10} = 5325_7
$$

Therefore:

$$
6241_7 - 613_7 = 5325_7
$$

Using vertical form:
- Borrow according to base $7$.
- Use $7$ when borrowing.

$$
7 + 1 - 3 = 5_7
$$

$$
3 - 1 = 2_7
$$

$$
7 + 2 - 6 = 3_7
$$

Therefore:

$$
6241_7 - 613_7 = 5325_7
$$

### Worked Example:
Calculate $372_8 - 77_8$.

Using conversion of base:

$$
372_8 = 250_{10}
$$

$$
77_8 = 63_{10}
$$

$$
250 - 63 = 187_{10}
$$

Convert $187_{10}$ to base $8$:

$$
187_{10} = 273_8
$$

Therefore:

$$
372_8 - 77_8 = 273_8
$$

### Common Mistakes & Exam Tips:
- When borrowing in base $8$, add $8$, not $10$.
- When borrowing in base $7$, add $7$, not $10$.
- The final answer must only contain digits allowed in that base.
- Convert to base $10$ if the borrowing process becomes confusing.

## Concept: Solving Problems Involving Number Bases
Number bases can be used in word problems involving quantities, percentages, money, measurements, and comparisons.

**Key Rules / Methods:**
- Read the problem carefully and identify values that need conversion.
- Convert percentages or fractions into actual quantities first.
- Convert the required values into the requested base.
- Use addition or subtraction in the stated base if needed.
- Give the final answer in the base requested by the question.

### Worked Example:
A study shows the modes of transportation used by $200$ pupils to go to school every day.

| Mode of Transportation | Percentage |
|---|---:|
| Bus | $25\%$ |
| Car | $40\%$ |
| Walking | $17\%$ |
| Bicycle | $10\%$ |
| Motorcycle | $8\%$ |

(a) State the number of pupils who go to school by bus and by car in base $4$.

Bus:

$$
\frac{25}{100} \times 200 = 50_{10}
$$

Convert $50_{10}$ to base $4$:

$$
50_{10} = 302_4
$$

Car:

$$
\frac{40}{100} \times 200 = 80_{10}
$$

Convert $80_{10}$ to base $4$:

$$
80_{10} = 1100_4
$$

Therefore, the number of pupils who go by bus is $302_4$, and the number who go by car is $1100_4$.

(b) Calculate the total number of pupils who go to school by bus and by car in base $4$.

$$
1100_4 + 302_4 = 2002_4
$$

Therefore, the total number of pupils is $2002_4$.

(c) Calculate the difference in number of pupils, in base $7$, between those who walk to school and those who go by motorcycle.

Walking:

$$
\frac{17}{100} \times 200 = 34_{10}
$$

Motorcycle:

$$
\frac{8}{100} \times 200 = 16_{10}
$$

Difference:

$$
34 - 16 = 18_{10}
$$

Convert $18_{10}$ to base $7$:

$$
18_{10} = 24_7
$$

Therefore, the difference is $24_7$.

### Common Mistakes & Exam Tips:
- Do not convert the percentage directly into another base before finding the actual quantity.
- Always answer in the base requested by the question.
- For comparison questions, it is usually easier to convert all values to base $10$ first.