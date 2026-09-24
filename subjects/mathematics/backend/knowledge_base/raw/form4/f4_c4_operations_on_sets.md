# Topic: Operations on Sets
**Form:** Form 4 | **Chapter:** Chapter 4 | **Curriculum:** SPM KSSM

## Overview
Operations on sets are used to represent, group, compare, and analyse data. In this topic, students learn about intersection of sets, union of sets, complements, combined operations on sets, and solving word problems using Venn diagrams.

## Concept: Intersection of Sets
The intersection of two sets contains the common elements that are found in both sets.

**Key Rules / Methods:**
- The intersection of set $P$ and set $Q$ is written as:

$$
P \cap Q
$$

- $P \cap Q$ means the elements that are in both set $P$ and set $Q$.
- An intersection exists when there is more than one set.
- For three sets, the intersection is written as:

$$
P \cap Q \cap R
$$

- $P \cap Q \cap R$ means the elements that are common to all three sets.

### Worked Example:
It is given that:

$$
\xi = \{x : x \text{ is an integer},\ 1 \leq x \leq 10\}
$$

$$
P = \{x : x \text{ is an odd number}\}
$$

$$
Q = \{x : x \text{ is a prime number}\}
$$

$$
R = \{x : x \text{ is a multiple of } 3\}
$$

List all the elements of $P \cap Q$, $P \cap R$, $Q \cap R$, and $P \cap Q \cap R$.

First, list the elements of each set:

$$
P = \{1, 3, 5, 7, 9\}
$$

$$
Q = \{2, 3, 5, 7\}
$$

$$
R = \{3, 6, 9\}
$$

Find the common elements:

$$
P \cap Q = \{3, 5, 7\}
$$

$$
P \cap R = \{3, 9\}
$$

$$
Q \cap R = \{3\}
$$

$$
P \cap Q \cap R = \{3\}
$$

Therefore:

$$
n(P \cap Q) = 3
$$

$$
n(P \cap R) = 2
$$

$$
n(Q \cap R) = 1
$$

$$
n(P \cap Q \cap R) = 1
$$

### Common Mistakes & Exam Tips:
- Intersection means common elements only.
- Do not include elements that appear in only one set.
- For $P \cap Q \cap R$, the element must appear in all three sets.
- Always list the elements of each set first before finding the intersection.

## Concept: Intersection of Sets Using Venn Diagrams
A Venn diagram can be used to represent intersections visually.

**Key Rules / Methods:**
- $P \cap Q$ is the overlapping region between sets $P$ and $Q$.
- $P \cap Q \cap R$ is the region where all three sets overlap.
- If one set is inside another set, then the smaller set may be the intersection.
- If two sets have no common elements, their intersection is an empty set.

### Important Set Ideas:
- A subset means all elements of one set are also found in another set.
- If set $B$ is a subset of set $A$, it is written as:

$$
B \subset A
$$

- An empty set has no elements.
- An empty set is written as:

$$
\varnothing
$$

or

$$
\{\}
$$

### Worked Example:
It is given that:

$$
A = \{\text{numbers on a dice}\}
$$

$$
B = \{\text{even numbers on a dice}\}
$$

$$
C = \{7, 8, 9\}
$$

List all the elements of $A \cap B$, $B \cap C$, and $A \cap C$.

First, list the elements:

$$
A = \{1, 2, 3, 4, 5, 6\}
$$

$$
B = \{2, 4, 6\}
$$

$$
C = \{7, 8, 9\}
$$

Since all elements of $B$ are found in $A$:

$$
A \cap B = \{2, 4, 6\}
$$

Since $B$ and $C$ have no common elements:

$$
B \cap C = \{\}
$$

Since $A$ and $C$ have no common elements:

$$
A \cap C = \varnothing
$$

### Common Mistakes & Exam Tips:
- If all elements of set $B$ are inside set $A$, then $A \cap B = B$.
- If two sets do not overlap, their intersection is $\varnothing$ or $\{\}$.
- Do not confuse subset with intersection.

## Concept: Complement of an Intersection of Sets
The complement of an intersection of sets refers to all elements in the universal set that are not in the intersection.

**Key Rules / Methods:**
- The complement of $A \cap B$ is written as:

$$
(A \cap B)'
$$

- $(A \cap B)'$ means all elements not in $A \cap B$.
- Always find the intersection first, then find its complement.
- Complements must be taken from the universal set $\xi$.

### Worked Example:
Given:

$$
\xi = \{x : x \text{ is an integer},\ 1 \leq x \leq 8\}
$$

$$
A = \{1, 2, 3, 4, 5, 6\}
$$

$$
B = \{2, 4, 6\}
$$

$$
C = \{1, 2, 3, 4\}
$$

List all the elements and state the number of elements of $(A \cap B)'$, $(A \cap C)'$, and $(A \cap B \cap C)'$.

First:

$$
\xi = \{1, 2, 3, 4, 5, 6, 7, 8\}
$$

Find $A \cap B$:

$$
A \cap B = \{2, 4, 6\}
$$

Therefore:

$$
(A \cap B)' = \{1, 3, 5, 7, 8\}
$$

$$
n(A \cap B)' = 5
$$

Find $A \cap C$:

$$
A \cap C = \{1, 2, 3, 4\}
$$

Therefore:

$$
(A \cap C)' = \{5, 6, 7, 8\}
$$

$$
n(A \cap C)' = 4
$$

Find $A \cap B \cap C$:

$$
A \cap B \cap C = \{2, 4\}
$$

Therefore:

$$
(A \cap B \cap C)' = \{1, 3, 5, 6, 7, 8\}
$$

$$
n(A \cap B \cap C)' = 6
$$

### Common Mistakes & Exam Tips:
- Do not find the complement before finding the intersection.
- $(A \cap B)'$ is not the same as $A' \cap B'$.
- The complement must be chosen from the universal set $\xi$.

## Concept: Solving Problems Involving Intersection of Sets
Venn diagrams are useful for solving word problems involving two or more sets.

**Key Rules / Methods:**
- Draw a Venn diagram.
- Fill the intersection first.
- Then fill the “only” regions.
- Add all regions inside the sets to find the total number involved.
- Subtract from the universal set to find the number not involved.

### Worked Example:
A total of $140$ Form 5 pupils are given the opportunity to attend intensive classes for History and Bahasa Melayu.

$65$ pupils choose Bahasa Melayu.

$70$ pupils choose History.

$50$ pupils choose both Bahasa Melayu and History.

Calculate:
(a) the total number of pupils who attend the intensive classes.

(b) the total number of pupils who do not attend any intensive classes.

Let:

$$
\xi = \{\text{total number of pupils}\}
$$

$$
B = \{\text{pupils who attend Bahasa Melayu class}\}
$$

$$
H = \{\text{pupils who attend History class}\}
$$

Given:

$$
n(\xi) = 140
$$

$$
n(B) = 65
$$

$$
n(H) = 70
$$

$$
n(B \cap H) = 50
$$

Bahasa Melayu only:

$$
65 - 50 = 15
$$

History only:

$$
70 - 50 = 20
$$

Total pupils who attend intensive classes:

$$
15 + 50 + 20 = 85
$$

Pupils who do not attend any intensive classes:

$$
140 - 85 = 55
$$

Therefore, $85$ pupils attend the intensive classes and $55$ pupils do not attend any intensive classes.

### Common Mistakes & Exam Tips:
- Always put the intersection value first.
- “Both” means intersection.
- “Only” means exclude the overlapping part.
- “Do not attend any” means outside all sets.

## Concept: Union of Sets
The union of two sets contains all elements that are in either set or in both sets.

**Key Rules / Methods:**
- The union of set $P$ and set $Q$ is written as:

$$
P \cup Q
$$

- $P \cup Q$ means all elements in set $P$, set $Q$, or both sets.
- For three sets:

$$
P \cup Q \cup R
$$

means all elements in $P$, $Q$, or $R$.

### Worked Example:
It is given that:

$$
P = \{\text{factors of } 24\}
$$

$$
Q = \{\text{multiples of } 3 \text{ which are less than } 20\}
$$

$$
R = \{\text{multiples of } 4 \text{ which are less than } 20\}
$$

List all the elements of $P \cup Q$, $P \cup R$, $Q \cup R$, and $P \cup Q \cup R$.

First:

$$
P = \{1, 2, 3, 4, 6, 8, 12, 24\}
$$

$$
Q = \{3, 6, 9, 12, 15, 18\}
$$

$$
R = \{4, 8, 12, 16\}
$$

Then:

$$
P \cup Q = \{1, 2, 3, 4, 6, 8, 9, 12, 15, 18, 24\}
$$

$$
P \cup R = \{1, 2, 3, 4, 6, 8, 12, 16, 24\}
$$

$$
Q \cup R = \{3, 4, 6, 8, 9, 12, 15, 16, 18\}
$$

$$
P \cup Q \cup R = \{1, 2, 3, 4, 6, 8, 9, 12, 15, 16, 18, 24\}
$$

### Common Mistakes & Exam Tips:
- Union means combine all elements.
- Do not repeat the same element twice.
- Elements that appear in both sets are written once only.
- Union includes the overlapping and non-overlapping regions.

## Concept: Union of Sets Using Venn Diagrams
The union of sets is represented by shading all regions that belong to at least one of the sets.

**Key Rules / Methods:**
- $P \cup Q$ means shade all of set $P$ and all of set $Q$.
- $P \cup Q \cup R$ means shade all three sets.
- The region outside the sets is not included in the union.
- If $\xi = P \cup Q \cup R$, then every element in the universal set belongs to at least one of the sets.

### Common Mistakes & Exam Tips:
- Do not shade only the overlapping region for union.
- Union includes “either one or both”.
- In word problems, “or” usually means union.

## Concept: Complement of a Union of Sets
The complement of a union of sets refers to all elements in the universal set that are not in any of the sets being joined.

**Key Rules / Methods:**
- The complement of $A \cup B$ is written as:

$$
(A \cup B)'
$$

- $(A \cup B)'$ means all elements not in set $A$ and not in set $B$.
- For three sets:

$$
(A \cup B \cup C)'
$$

means all elements outside $A$, $B$, and $C$.
- Always find the union first, then find its complement.

### Worked Example:
Given:

$$
\xi = \{x : x \text{ is an integer},\ 50 \leq x \leq 60\}
$$

$$
G = \{x : x \text{ is a prime number}\}
$$

$$
H = \{x : x \text{ is a multiple of } 4\}
$$

$$
I = \{x : x \text{ is a multiple of } 5\}
$$

List all the elements and state the number of elements of $(G \cup H)'$, $(G \cup I)'$, $(H \cup I)'$, and $(G \cup H \cup I)'$.

First:

$$
\xi = \{50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60\}
$$

$$
G = \{53, 59\}
$$

$$
H = \{52, 56, 60\}
$$

$$
I = \{50, 55, 60\}
$$

Find $(G \cup H)'$:

$$
G \cup H = \{52, 53, 56, 59, 60\}
$$

$$
(G \cup H)' = \{50, 51, 54, 55, 57, 58\}
$$

$$
n(G \cup H)' = 6
$$

Find $(G \cup I)'$:

$$
G \cup I = \{50, 53, 55, 59, 60\}
$$

$$
(G \cup I)' = \{51, 52, 54, 56, 57, 58\}
$$

$$
n(G \cup I)' = 6
$$

Find $(H \cup I)'$:

$$
H \cup I = \{50, 52, 55, 56, 60\}
$$

$$
(H \cup I)' = \{51, 53, 54, 57, 58, 59\}
$$

$$
n(H \cup I)' = 6
$$

Find $(G \cup H \cup I)'$:

$$
G \cup H \cup I = \{50, 52, 53, 55, 56, 59, 60\}
$$

$$
(G \cup H \cup I)' = \{51, 54, 57, 58\}
$$

$$
n(G \cup H \cup I)' = 4
$$

### Common Mistakes & Exam Tips:
- $(A \cup B)'$ means outside both $A$ and $B$.
- Do not include elements that are inside any of the sets.
- Always use the universal set to find the complement.

## Concept: Solving Problems Involving Union of Sets
Union problems often involve finding the number of people or objects in at least one category.

**Key Rules / Methods:**
For two sets:

$$
n(A \cup B) = n(A) + n(B) - n(A \cap B)
$$

For three sets:

$$
n(A \cup B \cup C)
$$

can be found by filling a Venn diagram region by region.

**Steps for three-set Venn diagram problems:**
- Fill the centre region first.
- Subtract the centre from each “both” region.
- Find each “only” region.
- Add all regions inside the sets.
- Subtract from the total if asked for those who do not choose any category.

### Worked Example:
A total of $26$ pupils participate in a scouting programme at the river bank. The activities are kayaking and fishing.

$18$ pupils participate in kayaking.

$15$ pupils participate in fishing.

$9$ pupils participate in both kayaking and fishing.

Find the total number of pupils who participate in the activities.

Let:

$$
A = \{\text{pupils who participate in kayaking}\}
$$

$$
B = \{\text{pupils who participate in fishing}\}
$$

Kayaking only:

$$
18 - 9 = 9
$$

Fishing only:

$$
15 - 9 = 6
$$

Total who participate in at least one activity:

$$
n(A \cup B) = 9 + 9 + 6
$$

$$
= 24
$$

Therefore, $24$ pupils participate in the activities.

Number of pupils who do not participate:

$$
26 - 24 = 2
$$

### Worked Example:
A total of $100$ adults are involved in a survey on their top choices of reading materials.

$40$ choose newspapers.

$25$ choose magazines.

$18$ choose storybooks.

$8$ choose both newspapers and magazines.

$7$ choose both magazines and storybooks.

$5$ choose both newspapers and storybooks.

$3$ choose all three types of reading materials.

How many people do not choose any of the reading materials?

Let:

$$
P = \{\text{newspapers}\}
$$

$$
Q = \{\text{magazines}\}
$$

$$
R = \{\text{storybooks}\}
$$

All three:

$$
n(P \cap Q \cap R) = 3
$$

Newspapers and magazines only:

$$
8 - 3 = 5
$$

Magazines and storybooks only:

$$
7 - 3 = 4
$$

Newspapers and storybooks only:

$$
5 - 3 = 2
$$

Newspapers only:

$$
40 - 5 - 3 - 2 = 30
$$

Magazines only:

$$
25 - 5 - 3 - 4 = 13
$$

Storybooks only:

$$
18 - 3 - 4 - 2 = 9
$$

Total who choose at least one reading material:

$$
30 + 13 + 9 + 5 + 4 + 2 + 3 = 66
$$

People who do not choose any reading material:

$$
100 - 66 = 34
$$

Therefore, $34$ people do not choose any of the reading materials.

### Common Mistakes & Exam Tips:
- “Both newspapers and magazines” usually includes those who choose all three unless the word “only” is stated.
- Always subtract the centre value from each pairwise overlap.
- Do not count the centre region more than once.

## Concept: Combined Operations on Sets
Combined operations on sets involve both intersection and union at the same time.

**Key Rules / Methods:**
- Combined operations involve both $\cap$ and $\cup$.
- If there are brackets, solve the operation inside the brackets first.
- If there are no brackets, solve from left to right.
- In Venn diagrams, shade each part step by step.

### Worked Example:
The table below shows the hobbies of a group of pupils.

$$
P = \{\text{pupils who like singing}\}
$$

$$
Q = \{\text{pupils who like dancing}\}
$$

$$
R = \{\text{pupils who like drawing}\}
$$

Given:

$$
P = \{\text{Arif, Emy, Iris, Alan, Jay}\}
$$

$$
Q = \{\text{Lily, Emy, Iris, Alan, May, Nani}\}
$$

$$
R = \{\text{Zarif, Getha, Iris, May, Jay}\}
$$

List all the elements of $(P \cup Q) \cap R$ and $Q \cup (P \cap R)$.

First, find $(P \cup Q) \cap R$.

Find $P \cup Q$:

$$
P \cup Q = \{\text{Arif, Emy, Iris, Alan, Jay, Lily, May, Nani}\}
$$

Then intersect with $R$:

$$
R = \{\text{Zarif, Getha, Iris, May, Jay}\}
$$

$$
(P \cup Q) \cap R = \{\text{Jay, Iris, May}\}
$$

Next, find $Q \cup (P \cap R)$.

Find $P \cap R$:

$$
P \cap R = \{\text{Iris, Jay}\}
$$

Then join with $Q$:

$$
Q = \{\text{Lily, Emy, Iris, Alan, May, Nani}\}
$$

$$
Q \cup (P \cap R) = \{\text{Lily, Emy, Iris, Alan, May, Nani, Jay}\}
$$

### Common Mistakes & Exam Tips:
- Brackets must be solved first.
- $(P \cup Q) \cap R$ is not the same as $P \cup (Q \cap R)$.
- For combined operations, write the intermediate set before writing the final answer.
- In Venn diagrams, shade step by step to avoid confusion.

## Concept: Complement of Combined Operations on Sets
The complement of combined operations on sets involves complements together with union and intersection.

**Key Rules / Methods:**
- The complement of set $A$ is written as $A'$.
- $A'$ means all elements in the universal set that are not in $A$.
- For expressions with brackets, solve the bracket first.
- Then apply the complement.
- Then continue with the union or intersection.

### Worked Example:
It is given that:

$$
\xi = \{x : x \text{ is an integer},\ 30 \leq x \leq 40\}
$$

$$
A = \{x : x \text{ is a multiple of } 3\}
$$

$$
B = \{x : x \text{ is a number such that the sum of its two digits is odd}\}
$$

$$
C = \{30, 32, 35, 39, 40\}
$$

List all the elements of:

$$
(A \cup B)' \cap C
$$

$$
A' \cap (B \cup C)
$$

$$
(A \cap C)' \cup (B \cap C)
$$

First:

$$
\xi = \{30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40\}
$$

$$
A = \{30, 33, 36, 39\}
$$

$$
B = \{30, 32, 34, 36, 38\}
$$

$$
C = \{30, 32, 35, 39, 40\}
$$

Find $(A \cup B)' \cap C$.

$$
A \cup B = \{30, 32, 33, 34, 36, 38, 39\}
$$

$$
(A \cup B)' = \{31, 35, 37, 40\}
$$

$$
(A \cup B)' \cap C = \{35, 40\}
$$

Find $A' \cap (B \cup C)$.

$$
A' = \{31, 32, 34, 35, 37, 38, 40\}
$$

$$
B \cup C = \{30, 32, 34, 35, 36, 38, 39, 40\}
$$

$$
A' \cap (B \cup C) = \{32, 34, 35, 38, 40\}
$$

Find $(A \cap C)' \cup (B \cap C)$.

$$
A \cap C = \{30, 39\}
$$

$$
(A \cap C)' = \{31, 32, 33, 34, 35, 36, 37, 38, 40\}
$$

$$
B \cap C = \{30, 32\}
$$

$$
(A \cap C)' \cup (B \cap C) = \{30, 31, 32, 33, 34, 35, 36, 37, 38, 40\}
$$

### Common Mistakes & Exam Tips:
- For $(A \cup B)'$, find $A \cup B$ first, then take the complement.
- For $(A \cap C)'$, find $A \cap C$ first, then take the complement.
- Complements must always be based on the universal set.
- Do not ignore brackets.

## Concept: Solving Problems Involving Combined Operations on Sets
Combined set problems often involve three categories and require careful use of “only”, “both”, and “all three”.

**Key Rules / Methods:**
- Fill the centre of the Venn diagram first.
- If “both A and B” includes all three, subtract the centre to get “A and B only”.
- If the question already says “A and B only”, do not subtract the centre.
- Find the “only” values for each set.
- Add the required regions based on the question.

### Worked Example:
The Residents’ Association of Happy Garden organises sports competitions.

$35$ participants join football.

$24$ participants join table tennis.

$13$ participants join badminton.

$4$ participants join both football and table tennis.

$8$ participants join both table tennis and badminton.

$2$ participants join all three competitions.

There is no participant joining badminton and football only.

Calculate the total number of participants who join one competition only.

Let:

$$
A = \{\text{participants who join football}\}
$$

$$
B = \{\text{participants who join table tennis}\}
$$

$$
C = \{\text{participants who join badminton}\}
$$

Given:

$$
n(A) = 35
$$

$$
n(B) = 24
$$

$$
n(C) = 13
$$

$$
n(A \cap B) = 4
$$

$$
n(B \cap C) = 8
$$

$$
n(A \cap B \cap C) = 2
$$

$$
n(A \cap C \text{ only}) = 0
$$

Football and table tennis only:

$$
4 - 2 = 2
$$

Table tennis and badminton only:

$$
8 - 2 = 6
$$

Badminton and football only:

$$
0
$$

Football only:

$$
35 - 2 - 2 - 0 = 31
$$

Badminton only:

$$
13 - 6 - 2 - 0 = 5
$$

Table tennis only:

$$
24 - 2 - 6 - 2 = 14
$$

Total number of participants who join one competition only:

$$
31 + 14 + 5 = 50
$$

Therefore, $50$ participants join one competition only.

### Common Mistakes & Exam Tips:
- Read carefully whether the question says “both” or “both only”.
- If “both” includes all three, subtract the centre value.
- Fill the Venn diagram from the most specific region to the least specific region.
- “One competition only” means add only the non-overlapping parts of each set.