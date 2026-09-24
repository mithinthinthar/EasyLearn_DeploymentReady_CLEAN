# Topic: Matrices
**Form:** Form 5 | **Chapter:** Chapter 2 | **Curriculum:** SPM KSSM

## Overview
Matrices are rectangular or square arrangements of numbers in rows and columns. In this topic, students learn how to represent information using matrices, identify the order and elements of matrices, determine equal matrices, perform basic matrix operations, multiply matrices, identify identity matrices, find inverse matrices, and solve simultaneous linear equations using the matrix method.

## Concept: Matrix
A matrix is a set of numbers arranged in rows and columns to form a rectangular or square array.

**Key Rules / Methods:**
- A matrix is usually written using square brackets.
- A matrix is usually represented by a capital letter such as $A$, $B$, $C$, or $D$.
- Numbers inside a matrix are called elements.
- Horizontal arrangements are called rows.
- Vertical arrangements are called columns.

### Example:
The matrix below has $2$ rows and $3$ columns:

$$
A =
\begin{bmatrix}
16 & 18 & 11 \\
5 & 10 & 4
\end{bmatrix}
$$

### Common Mistakes & Exam Tips:
- Do not confuse rows and columns.
- Rows go from left to right.
- Columns go from top to bottom.
- Always keep the original arrangement of data clear when forming a matrix.

## Concept: Representing Information in Matrix Form
Real-life information from tables can be represented in matrix form.

**Key Rules / Methods:**
- Each row can represent a category, person, place, or item.
- Each column can represent another category, time period, subject, or type.
- The matrix should follow the same order as the table unless another arrangement is clearly stated.

### Worked Example:
A shop records sales of three types of fans in March.

| Sale type | Stand fan | Ceiling fan | Wall fan |
|---|---:|---:|---:|
| In-store | $16$ | $18$ | $11$ |
| Online | $5$ | $10$ | $4$ |

The information can be written as:

$$
\begin{bmatrix}
16 & 18 & 11 \\
5 & 10 & 4
\end{bmatrix}
$$

### Common Mistakes & Exam Tips:
- State clearly what each row and column represents.
- Do not randomly switch rows and columns unless the question allows another arrangement.
- A table can sometimes be represented in more than one valid matrix form, depending on how rows and columns are assigned.

## Concept: Types of Matrices
Matrices can be classified based on their number of rows and columns.

### Row Matrix
A row matrix has only one row.

Example:

$$
\begin{bmatrix}
1700 & 2100 & 2000 & 1800
\end{bmatrix}
$$

### Column Matrix
A column matrix has only one column.

Example:

$$
\begin{bmatrix}
1700 \\
2100 \\
2000 \\
1800
\end{bmatrix}
$$

### Square Matrix
A square matrix has the same number of rows and columns.

Example:

$$
\begin{bmatrix}
13 & 5 & 1 \\
10 & 2 & 4 \\
8 & 8 & 9
\end{bmatrix}
$$

This is a $3 \times 3$ square matrix.

### Rectangular Matrix
A rectangular matrix has a different number of rows and columns.

Example:

$$
\begin{bmatrix}
76 & 82 & 72 \\
80 & 88 & 70
\end{bmatrix}
$$

This is a $2 \times 3$ rectangular matrix.

### Zero Matrix
A zero matrix is a matrix in which all elements are zero.

Example:

$$
O =
\begin{bmatrix}
0 & 0 \\
0 & 0
\end{bmatrix}
$$

### Common Mistakes & Exam Tips:
- A $1 \times 1$ matrix can be considered a square matrix.
- A row matrix has order $1 \times n$.
- A column matrix has order $m \times 1$.
- A zero matrix can have any order.

## Concept: Order of a Matrix
The order of a matrix is determined by the number of rows followed by the number of columns.

**Key Formula:**

$$
\text{Order of matrix} = \text{number of rows} \times \text{number of columns}
$$

If a matrix has $m$ rows and $n$ columns, its order is:

$$
m \times n
$$

### Worked Example:
Given:

$$
A =
\begin{bmatrix}
16 & 18 & 11 \\
5 & 10 & 4
\end{bmatrix}
$$

The matrix has:
- $2$ rows.
- $3$ columns.

Therefore, the order is:

$$
2 \times 3
$$

### Common Mistakes & Exam Tips:
- Order is written as rows first, then columns.
- Do not write $3 \times 2$ for a matrix with $2$ rows and $3$ columns.
- Read $2 \times 3$ as “matrix $2$ by $3$”.

## Concept: Elements of a Matrix
Each number inside a matrix is called an element.

**Key Rules / Methods:**
- The element in the $i$th row and $j$th column of matrix $A$ is written as:

$$
a_{ij}
$$

where:
- $i$ is the row number.
- $j$ is the column number.

### General Matrix:
For matrix $A$:

$$
A =
\begin{bmatrix}
a_{11} & a_{12} & \cdots & a_{1n} \\
a_{21} & a_{22} & \cdots & a_{2n} \\
\vdots & \vdots & \ddots & \vdots \\
a_{m1} & a_{m2} & \cdots & a_{mn}
\end{bmatrix}
$$

### Worked Example:
Given:

$$
D =
\begin{bmatrix}
-2 & 5 \\
0 & 4 \\
1 & 9
\end{bmatrix}
$$

The order is:

$$
3 \times 2
$$

The elements are:

$$
d_{11} = -2
$$

because $-2$ is in row $1$, column $1$.

$$
d_{21} = 0
$$

because $0$ is in row $2$, column $1$.

$$
d_{32} = 9
$$

because $9$ is in row $3$, column $2$.

### Common Mistakes & Exam Tips:
- $a_{23}$ means row $2$, column $3$.
- Do not read $a_{23}$ as row $3$, column $2$.
- The first number in the subscript always refers to the row.

## Concept: Equal Matrices
Two matrices are equal if they have the same order and their corresponding elements are equal.

**Key Rules / Methods:**
For:

$$
A =
\begin{bmatrix}
a & b \\
c & d
\end{bmatrix}
$$

and:

$$
B =
\begin{bmatrix}
e & f \\
g & h
\end{bmatrix}
$$

If:

$$
A = B
$$

then:

$$
a=e,\quad b=f,\quad c=g,\quad d=h
$$

### Worked Example:
Given:

$$
P =
\begin{bmatrix}
x & 7 \\
0 & 5 - 3z
\end{bmatrix}
$$

and:

$$
Q =
\begin{bmatrix}
5 & y+1 \\
0 & 2z
\end{bmatrix}
$$

If $P=Q$, then compare corresponding elements:

$$
x = 5
$$

$$
7 = y + 1
$$

$$
5 - 3z = 2z
$$

Solve:

$$
y = 6
$$

$$
5 = 5z
$$

$$
z = 1
$$

Therefore:

$$
x = 5,\quad y = 6,\quad z = 1
$$

### Common Mistakes & Exam Tips:
- Matrices with different orders cannot be equal.
- Corresponding elements must be in the same position.
- Do not compare elements that are in different rows or columns.

## Concept: Addition of Matrices
Matrices can be added only if they have the same order.

**Key Rules / Methods:**
For:

$$
A =
\begin{bmatrix}
a_{11} & a_{12} \\
a_{21} & a_{22}
\end{bmatrix}
$$

and:

$$
B =
\begin{bmatrix}
b_{11} & b_{12} \\
b_{21} & b_{22}
\end{bmatrix}
$$

then:

$$
A+B =
\begin{bmatrix}
a_{11}+b_{11} & a_{12}+b_{12} \\
a_{21}+b_{21} & a_{22}+b_{22}
\end{bmatrix}
$$

### Worked Example:
Given:

$$
C =
\begin{bmatrix}
10 & -8 & 4 \\
6 & -11 & 7
\end{bmatrix}
$$

and:

$$
D =
\begin{bmatrix}
14 & -2 & 1 \\
-3 & 5 & 9
\end{bmatrix}
$$

Calculate $C+D$.

$$
C+D =
\begin{bmatrix}
10+14 & -8+(-2) & 4+1 \\
6+(-3) & -11+5 & 7+9
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
24 & -10 & 5 \\
3 & -6 & 16
\end{bmatrix}
$$

### Common Mistakes & Exam Tips:
- Addition is performed element by element.
- Matrices must have the same order.
- The answer has the same order as the original matrices.

## Concept: Subtraction of Matrices
Matrices can be subtracted only if they have the same order.

**Key Rules / Methods:**
For:

$$
A =
\begin{bmatrix}
a_{11} & a_{12} \\
a_{21} & a_{22}
\end{bmatrix}
$$

and:

$$
B =
\begin{bmatrix}
b_{11} & b_{12} \\
b_{21} & b_{22}
\end{bmatrix}
$$

then:

$$
A-B =
\begin{bmatrix}
a_{11}-b_{11} & a_{12}-b_{12} \\
a_{21}-b_{21} & a_{22}-b_{22}
\end{bmatrix}
$$

### Worked Example:
Using the same matrices:

$$
D-C =
\begin{bmatrix}
14-10 & -2-(-8) & 1-4 \\
-3-6 & 5-(-11) & 9-7
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
4 & 6 & -3 \\
-9 & 16 & 2
\end{bmatrix}
$$

### Common Mistakes & Exam Tips:
- Be careful when subtracting negative numbers.
- $A-B$ is generally not the same as $B-A$.
- Subtraction of matrices does not obey the commutative law.

## Concept: Matrix Equations Involving Addition and Subtraction
A matrix equation can be solved by comparing corresponding elements.

### Worked Example:
Given:

$$
D =
\begin{bmatrix}
2x-1 & -3 \\
-12 & 5+y
\end{bmatrix}
$$

$$
E =
\begin{bmatrix}
x & 2 \\
7 & y
\end{bmatrix}
$$

and:

$$
D+E =
\begin{bmatrix}
8 & -1 \\
-5 & 13
\end{bmatrix}
$$

Then:

$$
D+E =
\begin{bmatrix}
2x-1+x & -3+2 \\
-12+7 & 5+y+y
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
3x-1 & -1 \\
-5 & 5+2y
\end{bmatrix}
$$

Compare corresponding elements:

$$
3x-1 = 8
$$

$$
3x = 9
$$

$$
x = 3
$$

and:

$$
5+2y = 13
$$

$$
2y = 8
$$

$$
y = 4
$$

Therefore:

$$
x=3,\quad y=4
$$

### Common Mistakes & Exam Tips:
- Simplify the matrix expression first.
- Then compare corresponding elements.
- Make sure the matrices have the same order before comparing.

## Concept: Scalar Multiplication
Scalar multiplication means multiplying a matrix by a number.

**Key Rules / Methods:**
If:

$$
A =
\begin{bmatrix}
a & b \\
c & d
\end{bmatrix}
$$

then:

$$
nA =
n
\begin{bmatrix}
a & b \\
c & d
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
na & nb \\
nc & nd
\end{bmatrix}
$$

where $n$ is a scalar.

### Worked Example:
Given:

$$
D =
\begin{bmatrix}
-5 & 4 \\
2 & 1
\end{bmatrix}
$$

Calculate $3D$.

$$
3D =
3
\begin{bmatrix}
-5 & 4 \\
2 & 1
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
3(-5) & 3(4) \\
3(2) & 3(1)
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
-15 & 12 \\
6 & 3
\end{bmatrix}
$$

### Worked Example:
Calculate:

$$
-\frac{1}{2}D
$$

$$
-\frac{1}{2}D =
-\frac{1}{2}
\begin{bmatrix}
-5 & 4 \\
2 & 1
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
\frac{5}{2} & -2 \\
-1 & -\frac{1}{2}
\end{bmatrix}
$$

### Common Mistakes & Exam Tips:
- Multiply every element by the scalar.
- Do not multiply only the first row or first column.
- Be careful with negative signs and fractions.

## Concept: Laws of Matrix Operations
Matrix operations follow some arithmetic laws.

### Addition of Matrices
Addition obeys the commutative law:

$$
A+B = B+A
$$

Addition obeys the associative law:

$$
(A+B)+C = A+(B+C)
$$

### Subtraction of Matrices
Subtraction does not obey the commutative law:

$$
A-B \neq B-A
$$

Subtraction does not obey the associative law:

$$
(A-B)-C \neq A-(B-C)
$$

### Distributive Law
For scalar $h$:

$$
h(A+B)=hA+hB
$$

$$
h(A-B)=hA-hB
$$

### Zero Matrix
If $O$ is a zero matrix with the same order as $A$, then:

$$
A+O=A
$$

$$
A-O=A
$$

### Common Mistakes & Exam Tips:
- Addition behaves more like normal arithmetic than subtraction.
- Subtraction order matters.
- The zero matrix must have the correct order.

## Concept: Multiplication of Two Matrices
Matrix multiplication can be performed only if the number of columns in the first matrix equals the number of rows in the second matrix.

**Key Rule:**

If:

$$
A \text{ has order } m \times n
$$

and:

$$
B \text{ has order } n \times p
$$

then $AB$ can be performed and:

$$
AB \text{ has order } m \times p
$$

### Order Rule:

$$
(m \times n)(n \times p) = m \times p
$$

The inside numbers must be the same.

### Common Mistakes & Exam Tips:
- Always check the order before multiplying.
- $AB$ may be possible while $BA$ may not be possible.
- Even if both $AB$ and $BA$ are possible, they may not be equal.

## Concept: Row-by-Column Multiplication
Each element in the product matrix is found by multiplying a row from the first matrix with a column from the second matrix.

### Worked Example:
Given:

$$
A =
\begin{bmatrix}
2 & 3 \\
1 & 5
\end{bmatrix}
$$

and:

$$
B =
\begin{bmatrix}
6 & -7 \\
-2 & 1
\end{bmatrix}
$$

Calculate $AB$.

$$
AB =
\begin{bmatrix}
2 & 3 \\
1 & 5
\end{bmatrix}
\begin{bmatrix}
6 & -7 \\
-2 & 1
\end{bmatrix}
$$

First row, first column:

$$
(2)(6)+(3)(-2)=12-6=6
$$

First row, second column:

$$
(2)(-7)+(3)(1)=-14+3=-11
$$

Second row, first column:

$$
(1)(6)+(5)(-2)=6-10=-4
$$

Second row, second column:

$$
(1)(-7)+(5)(1)=-7+5=-2
$$

Therefore:

$$
AB =
\begin{bmatrix}
6 & -11 \\
-4 & -2
\end{bmatrix}
$$

### Common Mistakes & Exam Tips:
- Multiply row by column.
- Add the products after multiplying.
- Do not multiply corresponding elements only.
- Matrix multiplication is not the same as scalar multiplication.

## Concept: Matrix Multiplication Is Not Commutative
For matrices, generally:

$$
AB \neq BA
$$

Sometimes $AB$ exists but $BA$ does not exist.

### Example:
If $A$ has order $2 \times 3$ and $B$ has order $3 \times 1$:

$$
AB
$$

can be performed because:

$$
(2 \times 3)(3 \times 1)
$$

has matching inside numbers.

The result has order:

$$
2 \times 1
$$

But:

$$
BA
$$

has order arrangement:

$$
(3 \times 1)(2 \times 3)
$$

The inside numbers are $1$ and $2$, so $BA$ cannot be performed.

### Common Mistakes & Exam Tips:
- Do not assume $AB=BA$.
- Check both products separately.
- Matrix multiplication depends heavily on order.

## Concept: Matrix Powers
Matrix powers involve multiplying a square matrix by itself.

**Key Rules / Methods:**
If $L$ is a square matrix:

$$
L^2 = LL
$$

$$
L^3 = L^2L
$$

or:

$$
L^3 = LL^2
$$

### Common Mistakes & Exam Tips:
- $L^2$ does not mean squaring every element.
- You must multiply the matrix by itself.
- Matrix powers are only normally defined for square matrices.

### Example:
If:

$$
L =
\begin{bmatrix}
-4 & 2 \\
0 & 1
\end{bmatrix}
$$

then:

$$
L^2 = LL
$$

$$
=
\begin{bmatrix}
-4 & 2 \\
0 & 1
\end{bmatrix}
\begin{bmatrix}
-4 & 2 \\
0 & 1
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
16 & -6 \\
0 & 1
\end{bmatrix}
$$

### Common Mistakes & Exam Tips:
- Do not write:

$$
L^2 =
\begin{bmatrix}
(-4)^2 & 2^2 \\
0^2 & 1^2
\end{bmatrix}
$$

This is wrong.

## Concept: Applications of Matrix Multiplication
Matrix multiplication can be used to calculate total cost, total profit, total commission, and total investment.

### Worked Example:
A seller sells three types of goods for three days.

| Day | Goods A | Goods B | Goods C |
|---|---:|---:|---:|
| First day | $40$ | $28$ | $36$ |
| Second day | $42$ | $36$ | $30$ |
| Third day | $35$ | $25$ | $42$ |

The profit per item is:

$$
\begin{bmatrix}
5 \\
8 \\
6
\end{bmatrix}
$$

Total profit each day:

$$
\begin{bmatrix}
40 & 28 & 36 \\
42 & 36 & 30 \\
35 & 25 & 42
\end{bmatrix}
\begin{bmatrix}
5 \\
8 \\
6
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
40(5)+28(8)+36(6) \\
42(5)+36(8)+30(6) \\
35(5)+25(8)+42(6)
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
640 \\
678 \\
627
\end{bmatrix}
$$

Therefore, the total profits for the first, second, and third day are RM$640$, RM$678$, and RM$627$ respectively.

### Common Mistakes & Exam Tips:
- The quantity matrix usually goes first.
- The price or profit matrix is often written as a column matrix.
- Check that the order allows multiplication.

## Concept: Identity Matrix
An identity matrix is a square matrix with $1$ on the main diagonal and $0$ elsewhere.

**Key Rules / Methods:**
The $2 \times 2$ identity matrix is:

$$
I =
\begin{bmatrix}
1 & 0 \\
0 & 1
\end{bmatrix}
$$

The $3 \times 3$ identity matrix is:

$$
I =
\begin{bmatrix}
1 & 0 & 0 \\
0 & 1 & 0 \\
0 & 0 & 1
\end{bmatrix}
$$

For any suitable matrix $A$:

$$
AI = IA = A
$$

### Common Mistakes & Exam Tips:
- An identity matrix must be square.
- The main diagonal must contain only $1$.
- All other elements must be $0$.
- A diagonal matrix is not always an identity matrix, but an identity matrix is a diagonal matrix.

## Concept: Inverse Matrix
The inverse matrix of $A$ is written as $A^{-1}$.

**Key Rules / Methods:**
If $A^{-1}$ is the inverse of $A$, then:

$$
AA^{-1}=A^{-1}A=I
$$

where $I$ is the identity matrix.

### Common Mistakes & Exam Tips:
- $A^{-1}$ is read as “inverse matrix of $A$”.
- $A^{-1}$ does not mean $\frac{1}{A}$.
- Only square matrices may have inverse matrices.
- Not every square matrix has an inverse.

## Concept: Checking Whether Two Matrices Are Inverses
Two matrices are inverses of each other if their product gives the identity matrix.

### Worked Example:
Check whether:

$$
A =
\begin{bmatrix}
4 & 1 \\
7 & 2
\end{bmatrix}
$$

and:

$$
B =
\begin{bmatrix}
2 & -1 \\
-7 & 4
\end{bmatrix}
$$

are inverse matrices.

Calculate:

$$
AB =
\begin{bmatrix}
4 & 1 \\
7 & 2
\end{bmatrix}
\begin{bmatrix}
2 & -1 \\
-7 & 4
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
4(2)+1(-7) & 4(-1)+1(4) \\
7(2)+2(-7) & 7(-1)+2(4)
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
1 & 0 \\
0 & 1
\end{bmatrix}
$$

Since the product is the identity matrix, $B$ is the inverse matrix of $A$.

### Common Mistakes & Exam Tips:
- To confirm inverse matrices, check that the product is $I$.
- For square matrices, both $AB$ and $BA$ should give $I$.
- If the product is not $I$, they are not inverse matrices.

## Concept: Determinant of a $2 \times 2$ Matrix
For:

$$
A =
\begin{bmatrix}
a & b \\
c & d
\end{bmatrix}
$$

the determinant is:

$$
|A| = ad - bc
$$

### Common Mistakes & Exam Tips:
- Multiply the main diagonal first: $ad$.
- Multiply the other diagonal: $bc$.
- Then subtract:

$$
ad-bc
$$

- Do not calculate $ab-cd$.

## Concept: Existence of an Inverse Matrix
A $2 \times 2$ matrix has an inverse if its determinant is not zero.

**Key Rule:**
For:

$$
A =
\begin{bmatrix}
a & b \\
c & d
\end{bmatrix}
$$

the inverse exists if:

$$
ad-bc \neq 0
$$

The inverse does not exist if:

$$
ad-bc = 0
$$

### Worked Example:
Given:

$$
A =
\begin{bmatrix}
1 & 2 \\
4 & 8
\end{bmatrix}
$$

Find whether $A^{-1}$ exists.

Calculate determinant:

$$
ad-bc = 1(8)-2(4)
$$

$$
=8-8
$$

$$
=0
$$

Since the determinant is $0$, $A^{-1}$ does not exist.

### Worked Example:
Given:

$$
B =
\begin{bmatrix}
3 & 5 \\
2 & 4
\end{bmatrix}
$$

Calculate determinant:

$$
ad-bc = 3(4)-5(2)
$$

$$
=12-10
$$

$$
=2
$$

Since the determinant is not $0$, $B^{-1}$ exists.

### Common Mistakes & Exam Tips:
- Always check the determinant first.
- If determinant is $0$, stop. The inverse does not exist.
- Do not try to use the inverse formula when $ad-bc=0$.

## Concept: Formula for Inverse Matrix
For:

$$
A =
\begin{bmatrix}
a & b \\
c & d
\end{bmatrix}
$$

the inverse matrix is:

$$
A^{-1}
=
\frac{1}{ad-bc}
\begin{bmatrix}
d & -b \\
-c & a
\end{bmatrix}
$$

where:

$$
ad-bc \neq 0
$$

### Steps:
1. Find the determinant $ad-bc$.
2. Swap $a$ and $d$.
3. Change the signs of $b$ and $c$.
4. Multiply the matrix by $\frac{1}{ad-bc}$.

### Worked Example:
Given:

$$
C =
\begin{bmatrix}
2 & -6 \\
1 & -2
\end{bmatrix}
$$

Find $C^{-1}$.

First, find the determinant:

$$
ad-bc = 2(-2)-(-6)(1)
$$

$$
= -4+6
$$

$$
=2
$$

Use the formula:

$$
C^{-1}
=
\frac{1}{2}
\begin{bmatrix}
-2 & 6 \\
-1 & 2
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
-1 & 3 \\
-\frac{1}{2} & 1
\end{bmatrix}
$$

### Common Mistakes & Exam Tips:
- Swap $a$ and $d$.
- Change signs of $b$ and $c$.
- Do not change the signs of $a$ and $d$.
- Do not forget to multiply by $\frac{1}{ad-bc}$.

## Concept: Solving Matrix Equations Using Inverse Matrix
If:

$$
AX = I
$$

then:

$$
X = A^{-1}
$$

because multiplying a matrix by its inverse gives the identity matrix.

### Worked Example:
Given:

$$
\begin{bmatrix}
1 & 2 \\
3 & 8
\end{bmatrix}
A
=
\begin{bmatrix}
1 & 0 \\
0 & 1
\end{bmatrix}
$$

Find matrix $A$.

Since:

$$
\begin{bmatrix}
1 & 2 \\
3 & 8
\end{bmatrix}
A = I
$$

then $A$ is the inverse of:

$$
\begin{bmatrix}
1 & 2 \\
3 & 8
\end{bmatrix}
$$

So:

$$
A =
\frac{1}{1(8)-2(3)}
\begin{bmatrix}
8 & -2 \\
-3 & 1
\end{bmatrix}
$$

$$
=
\frac{1}{2}
\begin{bmatrix}
8 & -2 \\
-3 & 1
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
4 & -1 \\
-\frac{3}{2} & \frac{1}{2}
\end{bmatrix}
$$

### Common Mistakes & Exam Tips:
- Recognise that $AX=I$ means $X=A^{-1}$.
- Check the determinant before finding the inverse.
- The answer must have the same order as the square matrix.

## Concept: Matrix Form of Simultaneous Linear Equations
Simultaneous linear equations can be written in matrix form.

For:

$$
ax+by=p
$$

$$
cx+dy=q
$$

the matrix form is:

$$
\begin{bmatrix}
a & b \\
c & d
\end{bmatrix}
\begin{bmatrix}
x \\
y
\end{bmatrix}
=
\begin{bmatrix}
p \\
q
\end{bmatrix}
$$

This can be written as:

$$
AX=B
$$

where:

$$
A =
\begin{bmatrix}
a & b \\
c & d
\end{bmatrix}
$$

$$
X =
\begin{bmatrix}
x \\
y
\end{bmatrix}
$$

$$
B =
\begin{bmatrix}
p \\
q
\end{bmatrix}
$$

### Worked Example:
Write the following simultaneous equations in matrix form:

$$
3x+4y=12
$$

$$
5x-6y=7
$$

The matrix form is:

$$
\begin{bmatrix}
3 & 4 \\
5 & -6
\end{bmatrix}
\begin{bmatrix}
x \\
y
\end{bmatrix}
=
\begin{bmatrix}
12 \\
7
\end{bmatrix}
$$

### Common Mistakes & Exam Tips:
- Coefficients of $x$ go in the first column.
- Coefficients of $y$ go in the second column.
- Constants go in the column matrix on the right.
- Rearrange equations into standard form first.

## Concept: Solving Simultaneous Linear Equations Using Matrix Method
To solve:

$$
AX=B
$$

multiply both sides by $A^{-1}$:

$$
A^{-1}AX=A^{-1}B
$$

Since:

$$
A^{-1}A=I
$$

then:

$$
IX=A^{-1}B
$$

Therefore:

$$
X=A^{-1}B
$$

### General Formula:
For:

$$
ax+by=p
$$

$$
cx+dy=q
$$

we have:

$$
\begin{bmatrix}
x \\
y
\end{bmatrix}
=
\frac{1}{ad-bc}
\begin{bmatrix}
d & -b \\
-c & a
\end{bmatrix}
\begin{bmatrix}
p \\
q
\end{bmatrix}
$$

where:

$$
ad-bc \neq 0
$$

### Worked Example:
Solve using matrix method:

$$
x-2y=5
$$

$$
2x-3y=10
$$

Write in matrix form:

$$
\begin{bmatrix}
1 & -2 \\
2 & -3
\end{bmatrix}
\begin{bmatrix}
x \\
y
\end{bmatrix}
=
\begin{bmatrix}
5 \\
10
\end{bmatrix}
$$

Find the inverse of the coefficient matrix.

$$
ad-bc = 1(-3)-(-2)(2)
$$

$$
=-3+4
$$

$$
=1
$$

So:

$$
A^{-1}
=
\frac{1}{1}
\begin{bmatrix}
-3 & 2 \\
-2 & 1
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
-3 & 2 \\
-2 & 1
\end{bmatrix}
$$

Then:

$$
\begin{bmatrix}
x \\
y
\end{bmatrix}
=
\begin{bmatrix}
-3 & 2 \\
-2 & 1
\end{bmatrix}
\begin{bmatrix}
5 \\
10
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
-3(5)+2(10) \\
-2(5)+1(10)
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
5 \\
0
\end{bmatrix}
$$

Therefore:

$$
x=5,\quad y=0
$$

### Common Mistakes & Exam Tips:
- Matrix method requires the inverse of the coefficient matrix.
- The determinant must not be zero.
- Write the equations in the correct order before forming the matrix.
- Keep the order of multiplication as $A^{-1}B$, not $BA^{-1}$.

## Concept: Word Problems Using Matrix Method
Some word problems can be converted into simultaneous equations and solved using matrices.

### Worked Example:
A shop sells sardine curry puffs and potato curry puffs.

In the first hour:
- $24$ sardine curry puffs and $18$ potato curry puffs are sold.
- Total sales = RM$28.80$.

In the next hour:
- $30$ sardine curry puffs and $14$ potato curry puffs are sold.
- Total sales = RM$29.20$.

Let:
- $x$ = price of one sardine curry puff.
- $y$ = price of one potato curry puff.

Then:

$$
24x+18y=28.80
$$

$$
30x+14y=29.20
$$

Matrix form:

$$
\begin{bmatrix}
24 & 18 \\
30 & 14
\end{bmatrix}
\begin{bmatrix}
x \\
y
\end{bmatrix}
=
\begin{bmatrix}
28.80 \\
29.20
\end{bmatrix}
$$

Using the matrix method gives:

$$
x=0.60,\quad y=0.80
$$

Therefore:
- One sardine curry puff costs RM$0.60$.
- One potato curry puff costs RM$0.80$.

### Common Mistakes & Exam Tips:
- Define the variables clearly.
- Convert the word problem into two equations first.
- Then write the matrix form.
- Final answers should include units such as RM, kg, hours, or number of items.

## Concept: Summary of Matrix Operations
The main rules in this chapter are:

### Order of Matrix

$$
\text{Order} = \text{rows} \times \text{columns}
$$

### Element Notation

$$
a_{ij}
$$

means the element in row $i$, column $j$.

### Equal Matrices

$$
A=B
$$

only if both matrices have the same order and corresponding elements are equal.

### Addition and Subtraction

$$
A+B
$$

and:

$$
A-B
$$

can only be performed when $A$ and $B$ have the same order.

### Scalar Multiplication

$$
n
\begin{bmatrix}
a & b \\
c & d
\end{bmatrix}
=
\begin{bmatrix}
na & nb \\
nc & nd
\end{bmatrix}
$$

### Matrix Multiplication Order Rule

$$
(m \times n)(n \times p)=m \times p
$$

### Identity Matrix

$$
AI=IA=A
$$

### Inverse Matrix

$$
AA^{-1}=A^{-1}A=I
$$

### Determinant

$$
|A|=ad-bc
$$

### Inverse of $2 \times 2$ Matrix

$$
A^{-1}
=
\frac{1}{ad-bc}
\begin{bmatrix}
d & -b \\
-c & a
\end{bmatrix}
$$

where:

$$
ad-bc \neq 0
$$

### Matrix Method for Simultaneous Equations

$$
AX=B
$$

$$
X=A^{-1}B
$$

### Common Mistakes & Exam Tips:
- Always check matrix order before addition, subtraction, or multiplication.
- Addition and subtraction need the same order.
- Multiplication needs matching inside dimensions.
- Matrix multiplication is generally not commutative.
- $A^{-1}$ is not $\frac{1}{A}$.
- A matrix has no inverse if its determinant is zero.
- For simultaneous equations, arrange equations into standard form before forming the matrix.