# Topic: Probability of Combined Events
**Form:** Form 4 | **Chapter:** Chapter 9 | **Curriculum:** SPM KSSM

## Overview
Probability of combined events is used to calculate the chance of two or more events happening together or happening in a combined situation. In this topic, students learn about combined events, sample spaces, dependent events, independent events, mutually exclusive events, non-mutually exclusive events, tree diagrams, multiplication rule, addition rule, and solving probability problems involving combined events.

## Concept: Combined Events
Combined events are events formed by combining two or more events in one outcome.

**Key Rules / Methods:**
- A combined event may come from one experiment or more than one experiment.
- Outcomes of combined events can be written as ordered pairs.
- The sample space is the set of all possible outcomes.
- If event $A$ has $n(A)$ outcomes and event $B$ has $n(B)$ outcomes, then the total number of possible combined outcomes is:

$$
n(S) = n(A) \times n(B)
$$

where:
- $S$ is the sample space.
- $n(S)$ is the total number of outcomes in the sample space.

### Worked Example:
Two pupils play “Rock-Paper-Scissors”.

The possible outcomes are:

$$
\{(\text{Scissors}, \text{Rock}),\ (\text{Scissors}, \text{Paper}),\ (\text{Scissors}, \text{Scissors})\}
$$

$$
\{(\text{Rock}, \text{Scissors}),\ (\text{Rock}, \text{Paper}),\ (\text{Rock}, \text{Rock})\}
$$

$$
\{(\text{Paper}, \text{Scissors}),\ (\text{Paper}, \text{Rock}),\ (\text{Paper}, \text{Paper})\}
$$

There are $3$ choices for the first pupil and $3$ choices for the second pupil.

Therefore:

$$
n(S) = 3 \times 3 = 9
$$

### Common Mistakes & Exam Tips:
- Do not forget that order matters in ordered pairs.
- $(A,B)$ and $(B,A)$ may represent different outcomes.
- List all outcomes systematically to avoid missing any.

## Concept: Sample Space of Combined Events
A sample space contains all possible outcomes of an experiment.

**Key Rules / Methods:**
- The sample space is usually written as $S$.
- Outcomes of combined events are often written in ordered pairs.
- For two stages, write the first outcome first and the second outcome second.
- If the experiment is done without replacement, the same object cannot be chosen again.
- If the experiment is done with replacement, the same object may be chosen again.

### Worked Example:
Five cards labelled $T$, $E$, $K$, $U$, and $N$ are placed in a box. Two cards are taken out one by one without replacement.

The sample space is:

$$
S = \{(T,E),(T,K),(T,U),(T,N)\}
$$

$$
\cup \{(E,T),(E,K),(E,U),(E,N)\}
$$

$$
\cup \{(K,T),(K,E),(K,U),(K,N)\}
$$

$$
\cup \{(U,T),(U,E),(U,K),(U,N)\}
$$

$$
\cup \{(N,T),(N,E),(N,K),(N,U)\}
$$

Since there is no replacement, outcomes such as $(T,T)$ are not included.

### Worked Example:
Two coins are tossed. Let $T$ represent tail and $H$ represent head.

The sample space is:

$$
S = \{(T,T),(T,H),(H,T),(H,H)\}
$$

### Common Mistakes & Exam Tips:
- Without replacement means the first item is not returned before the second selection.
- With replacement means the first item is returned before the second selection.
- For coin tossing, $(T,H)$ and $(H,T)$ are different outcomes because the order is different.

## Concept: Probability of an Event
Probability measures the chance that an event will happen.

**Key Rules / Methods:**

$$
P(A) = \frac{n(A)}{n(S)}
$$

where:
- $P(A)$ is the probability of event $A$.
- $n(A)$ is the number of outcomes in event $A$.
- $n(S)$ is the number of outcomes in the sample space.

Probability values satisfy:

$$
0 \leq P(A) \leq 1
$$

- If $P(A) = 0$, event $A$ will definitely not occur.
- If $P(A) = 1$, event $A$ will definitely occur.

### Common Mistakes & Exam Tips:
- The denominator must be the total number of possible outcomes.
- Probability cannot be less than $0$ or more than $1$.
- Always simplify fractions when possible.

## Concept: Independent Events
Two events are independent if the occurrence of one event does not affect the occurrence of the other event.

**Key Rules / Methods:**
- Event $A$ and event $B$ are independent if event $A$ does not affect event $B$.
- With replacement usually gives independent events.
- Tossing a coin several times usually gives independent events.
- Rolling a dice several times usually gives independent events.

### Examples:
| Situation | Type |
|---|---|
| Tossing a fair coin twice | Independent events |
| Tossing a coin and rolling a dice | Independent events |
| Choosing a card, replacing it, then choosing again | Independent events |
| Answering several objective questions by random guessing | Independent events |

### Worked Example:
Identify whether the event is independent or dependent.

Obtain a tail twice when a fair coin is tossed twice.

This is an independent event because getting a tail in the first toss does not affect the probability of getting a tail in the second toss.

### Common Mistakes & Exam Tips:
- Repeated trials are not always dependent.
- If the first outcome does not change the sample space, the events are independent.
- “With replacement” normally means independent.

## Concept: Dependent Events
Two events are dependent if the occurrence of one event affects the occurrence of the other event.

**Key Rules / Methods:**
- Event $A$ and event $B$ are dependent if event $A$ affects event $B$.
- Without replacement usually gives dependent events.
- When the first selection changes the number of items left, the second probability changes.

### Examples:
| Situation | Type |
|---|---|
| Choosing two pens one by one without replacement | Dependent events |
| Choosing two cards without replacement | Dependent events |
| Choosing a marble and not returning it before choosing another | Dependent events |

### Worked Example:
A container contains $3$ red pens and $2$ blue pens. Two pens are taken out one by one without replacement.

This is a dependent event because the colour of the first pen affects the probability of the colour of the second pen.

### Common Mistakes & Exam Tips:
- “Without replacement” normally means dependent.
- After the first item is removed, the total number of items changes.
- Update the denominator and numerator for the second event.

## Concept: Multiplication Rule of Probability
The multiplication rule is used to find the probability that two events occur together.

**Key Rules / Methods:**
For independent events:

$$
P(A \cap B) = P(A) \times P(B)
$$

or:

$$
P(A \text{ and } B) = P(A) \times P(B)
$$

For three independent events:

$$
P(A \cap B \cap C) = P(A) \times P(B) \times P(C)
$$

### Worked Example:
Box $F$ contains seven cards labelled $P$, $A$, $M$, $E$, $R$, $A$, $N$.

Box $G$ contains five cards labelled $3$, $5$, $6$, $8$, $11$.

A card is chosen at random from each box. Find the probability of getting the letter $P$ and an even number.

Probability of getting $P$:

$$
P(P) = \frac{1}{7}
$$

Even numbers in box $G$ are $6$ and $8$.

$$
P(\text{even number}) = \frac{2}{5}
$$

Therefore:

$$
P(P \text{ and even number}) = \frac{1}{7} \times \frac{2}{5}
$$

$$
= \frac{2}{35}
$$

By listing possible outcomes:

$$
(P,6),\ (P,8)
$$

There are:

$$
7 \times 5 = 35
$$

possible outcomes.

Thus:

$$
P(P \text{ and even number}) = \frac{2}{35}
$$

Both methods give the same answer.

### Common Mistakes & Exam Tips:
- “And” usually means multiply when events are independent or when following a branch of a tree diagram.
- Check whether the events are independent or dependent first.
- For dependent events, the second probability may change.

## Concept: Probability of Independent Combined Events
For independent combined events, the probability of the first event does not affect the probability of the second event.

**Key Rules / Methods:**
- Identify each event.
- Find the probability of each event separately.
- Multiply the probabilities.

### Worked Example:
Box $A$ contains cards labelled $3$, $5$, $7$, and $9$.

Box $B$ contains cards labelled $X$, $Y$, and $Z$.

A card is chosen at random from each box. Find the probability of getting a factor of $9$ and the letter $Z$.

Factors of $9$ in box $A$ are $3$ and $9$.

$$
P(\text{factor of }9) = \frac{2}{4}
$$

Probability of getting $Z$:

$$
P(Z) = \frac{1}{3}
$$

Therefore:

$$
P(\text{factor of }9 \text{ and } Z) = \frac{2}{4} \times \frac{1}{3}
$$

$$
= \frac{1}{6}
$$

Alternative method:

Possible outcomes that satisfy the condition are:

$$
(3,Z),\ (9,Z)
$$

Total outcomes:

$$
4 \times 3 = 12
$$

Probability:

$$
\frac{2}{12} = \frac{1}{6}
$$

### Common Mistakes & Exam Tips:
- If items are selected from two different boxes, the events are usually independent.
- Count favourable outcomes carefully when using the listing method.
- Simplify the final probability.

## Concept: Tree Diagram
A tree diagram displays all possible outcomes of combined events.

**Key Rules / Methods:**
- Each branch represents one possible outcome.
- The probabilities are written on branches.
- To find the probability of an outcome, multiply probabilities along the branches.
- To find the probability of several outcomes, add the probabilities of the required branches.

### Common Mistakes & Exam Tips:
- Branch probabilities from the same point should add up to $1$.
- For dependent events, the probabilities on the second branch may change.
- For independent events, the second branch probabilities usually remain the same.

## Concept: Probability of Dependent Events Using a Tree Diagram
For dependent events, probabilities change after the first event.

**Key Rules / Methods:**
- Draw the first-stage branches.
- Update the number of items left for the second-stage branches.
- Multiply along the required branches.

### Worked Example:
A bag contains $8$ green marbles and $1$ red marble. Two marbles are chosen one by one without replacement.

Find the probability that both marbles are green.

For the first marble:

$$
P(G) = \frac{8}{9}
$$

After one green marble is chosen, there are $7$ green marbles left out of $8$ marbles.

For the second marble:

$$
P(G \mid \text{first is }G) = \frac{7}{8}
$$

Therefore:

$$
P(G,G) = \frac{8}{9} \times \frac{7}{8}
$$

$$
= \frac{7}{9}
$$

Find the probability that the second marble is red.

The second marble is red only in the outcome $(G,R)$ because there is only one red marble.

$$
P(G,R) = \frac{8}{9} \times \frac{1}{8}
$$

$$
= \frac{1}{9}
$$

### Common Mistakes & Exam Tips:
- Without replacement means the total number decreases after the first selection.
- Update the numerator and denominator correctly.
- Do not use the same probability for the second draw unless the first item is replaced.

## Concept: With Replacement and Without Replacement
Replacement affects whether events are independent or dependent.

**Key Rules / Methods:**
- With replacement:
  - The selected item is returned.
  - The sample space remains the same.
  - Events are usually independent.
- Without replacement:
  - The selected item is not returned.
  - The sample space changes.
  - Events are usually dependent.

### Example:
A box contains cards labelled $R$, $U$, $A$, $N$, $G$.

If two cards are chosen without replacement, the probability of getting a consonant on the second draw changes after the first draw.

If two cards are chosen with replacement, the probability of getting a consonant on the second draw remains the same as the first draw.

### Common Mistakes & Exam Tips:
- Always read whether the item is replaced.
- If the question says “returned to the box”, use with replacement.
- If the question says “without replacement”, adjust the second probability.

## Concept: Mutually Exclusive Events
Two events are mutually exclusive if they cannot happen at the same time.

**Key Rules / Methods:**
- Events $A$ and $B$ are mutually exclusive if there is no intersection between them.

$$
A \cap B = \varnothing
$$

- This means:

$$
P(A \cap B) = 0
$$

- If event $A$ happens, event $B$ cannot happen at the same time.

### Worked Example:
A ball labelled from $1$ to $9$ is chosen at random.

Let:
- $T$ be the event of getting an even number.
- $V$ be the event of getting a factor of $9$.

Then:

$$
T = \{2,4,6,8\}
$$

$$
V = \{1,3,9\}
$$

There is no common outcome.

Therefore:

$$
T \cap V = \varnothing
$$

So $T$ and $V$ are mutually exclusive events.

### Common Mistakes & Exam Tips:
- Mutually exclusive means the events cannot occur together.
- Check the intersection of the two events.
- If the intersection is empty, the events are mutually exclusive.

## Concept: Non-Mutually Exclusive Events
Two events are non-mutually exclusive if they can happen at the same time.

**Key Rules / Methods:**
- Events $A$ and $B$ are non-mutually exclusive if they have at least one common outcome.

$$
A \cap B \neq \varnothing
$$

- This means:

$$
P(A \cap B) \neq 0
$$

### Worked Example:
A ball labelled from $1$ to $9$ is chosen at random.

Let:
- $T$ be the event of getting an even number.
- $U$ be the event of getting a perfect square.

Then:

$$
T = \{2,4,6,8\}
$$

$$
U = \{1,4,9\}
$$

The common outcome is:

$$
T \cap U = \{4\}
$$

Therefore, $T$ and $U$ are non-mutually exclusive events.

### Common Mistakes & Exam Tips:
- Non-mutually exclusive events have overlap.
- If an outcome belongs to both events, subtract the overlap when using the addition rule.
- Do not double-count common outcomes.

## Concept: Addition Rule for Mutually Exclusive Events
For mutually exclusive events, the probability of event $A$ or event $B$ is the sum of their probabilities.

**Key Rules / Methods:**
If $A$ and $B$ are mutually exclusive:

$$
P(A \cup B) = P(A) + P(B)
$$

or:

$$
P(A \text{ or } B) = P(A) + P(B)
$$

### Worked Example:
Five cards labelled $C$, $I$, $N$, $T$, and $A$ are placed in a box. A card is chosen at random.

Find the probability that the card chosen is labelled with a consonant or the letter $A$.

Consonants:

$$
\{C,N,T\}
$$

Letter $A$:

$$
\{A\}
$$

These events are mutually exclusive.

$$
P(\text{consonant}) = \frac{3}{5}
$$

$$
P(A) = \frac{1}{5}
$$

Therefore:

$$
P(\text{consonant or }A) = \frac{3}{5} + \frac{1}{5}
$$

$$
= \frac{4}{5}
$$

### Common Mistakes & Exam Tips:
- Use this rule only when the events do not overlap.
- “Or” usually means union.
- If there is overlap, do not use simple addition only.

## Concept: Addition Rule for Non-Mutually Exclusive Events
For non-mutually exclusive events, subtract the overlap to avoid double-counting.

**Key Rules / Methods:**
If $A$ and $B$ are non-mutually exclusive:

$$
P(A \cup B) = P(A) + P(B) - P(A \cap B)
$$

or:

$$
P(A \text{ or } B) = P(A) + P(B) - P(A \text{ and } B)
$$

### Worked Example:
Eight cards labelled $4$, $5$, $6$, $7$, $8$, $9$, $10$, and $11$ are placed in a box.

A card is chosen at random.

Let:
- $A$ be the event of getting a number greater than $8$.
- $B$ be the event of getting a prime number.

Then:

$$
A = \{9,10,11\}
$$

$$
B = \{5,7,11\}
$$

The intersection is:

$$
A \cap B = \{11\}
$$

Therefore:

$$
P(A \cup B) = P(A) + P(B) - P(A \cap B)
$$

$$
= \frac{3}{8} + \frac{3}{8} - \frac{1}{8}
$$

$$
= \frac{5}{8}
$$

### Worked Example:
Using the same cards, let:
- $C$ be the event of getting an even number.

Then:

$$
C = \{4,6,8,10\}
$$

Find $P(A \cup C)$.

Intersection:

$$
A \cap C = \{10\}
$$

Therefore:

$$
P(A \cup C) = \frac{3}{8} + \frac{4}{8} - \frac{1}{8}
$$

$$
= \frac{6}{8}
$$

$$
= \frac{3}{4}
$$

### Common Mistakes & Exam Tips:
- Always check whether the events overlap.
- If there is overlap, subtract $P(A \cap B)$.
- The overlap is counted twice if it is not subtracted.

## Concept: Difference Between “And” and “Or” in Probability
The words “and” and “or” have specific meanings in probability.

**Key Rules / Methods:**
- “And” means intersection.

$$
A \text{ and } B = A \cap B
$$

- “Or” means union.

$$
A \text{ or } B = A \cup B
$$

- For independent events, “and” often uses multiplication.
- For mutually exclusive or non-mutually exclusive events, “or” often uses addition rule.

### Common Mistakes & Exam Tips:
- “And” usually means both events happen.
- “Or” means at least one of the events happens.
- Do not multiply for “or” questions unless using complement or another valid method.
- Do not add for “and” questions.

## Concept: Complement of an Event
The complement of an event is the event that the original event does not happen.

**Key Rules / Methods:**
- The complement of $A$ is written as:

$$
A'
$$

- The probability of the complement is:

$$
P(A') = 1 - P(A)
$$

- Complement method is useful for “at least one” questions.

### Worked Example:
The probability that a smartphone has a display problem is:

$$
\frac{2}{13}
$$

The probability that a smartphone has no display problem is:

$$
1 - \frac{2}{13} = \frac{11}{13}
$$

### Common Mistakes & Exam Tips:
- “At least one” can often be solved by finding $1 - P(\text{none})$.
- Make sure the event and its complement cover the whole sample space.
- Complement probability must also be between $0$ and $1$.

## Concept: Probability of “At Least One”
“At least one” means one or more.

**Key Rules / Methods:**
For two events:

$$
P(\text{at least one}) = 1 - P(\text{none})
$$

For two independent trials:

$$
P(\text{at least one success}) = 1 - P(\text{no success in both trials})
$$

### Worked Example:
The probability that a smartphone has a display problem is:

$$
\frac{2}{13}
$$

Two smartphones are chosen at random. Find the probability that at least one smartphone has a display problem.

Let:
- $M$ = has a display problem.
- $M'$ = no display problem.

Then:

$$
P(M) = \frac{2}{13}
$$

$$
P(M') = \frac{11}{13}
$$

At least one display problem means:

$$
(M,M),\ (M,M'),\ (M',M)
$$

Therefore:

$$
P(\text{at least one}) = \left(\frac{2}{13} \times \frac{2}{13}\right) + \left(\frac{2}{13} \times \frac{11}{13}\right) + \left(\frac{11}{13} \times \frac{2}{13}\right)
$$

$$
= \frac{48}{169}
$$

Using complement:

$$
P(\text{at least one}) = 1 - P(M',M')
$$

$$
= 1 - \left(\frac{11}{13} \times \frac{11}{13}\right)
$$

$$
= 1 - \frac{121}{169}
$$

$$
= \frac{48}{169}
$$

### Common Mistakes & Exam Tips:
- “At least one” does not mean exactly one.
- Use complement method to make the calculation shorter.
- For two trials, “none” means the event does not happen in both trials.

## Concept: Probability of “Only One”
“Only one” means exactly one event happens.

**Key Rules / Methods:**
For two events $A$ and $B$:

$$
P(\text{only }A) = P(A \cap B')
$$

$$
P(\text{only }B) = P(A' \cap B)
$$

Exactly one of $A$ and $B$ happens:

$$
P(A \cap B') + P(A' \cap B)
$$

### Worked Example:
If the probability that Kam Seng passes Physics is $0.58$ and the probability that he passes Chemistry is $0.42$, assuming the events are independent:

Probability of passing Physics only:

$$
0.58(1 - 0.42)
$$

Probability of passing Chemistry only:

$$
(1 - 0.58)(0.42)
$$

Probability of passing only one test:

$$
0.58(0.58) + 0.42(0.42)
$$

### Common Mistakes & Exam Tips:
- “Only one” is not the same as “at least one”.
- “Only Physics” means pass Physics and fail Chemistry.
- Read the wording carefully.

## Concept: Venn Diagrams in Probability
Venn diagrams can be used to show the relationship between events.

**Key Rules / Methods:**
- Overlapping regions represent intersections.
- Non-overlapping regions represent mutually exclusive events.
- The outside region represents neither event.
- The total probability in the universal set is $1$.

### Worked Example:
The probabilities that Zalifah and Maran eat cendol are:

$$
P(Z) = \frac{5}{7}
$$

$$
P(M) = \frac{3}{5}
$$

Assuming the events are independent:

$$
P(Z \cap M) = \frac{5}{7} \times \frac{3}{5}
$$

$$
= \frac{3}{7}
$$

Only Zalifah eats cendol:

$$
\frac{5}{7} - \frac{3}{7}
$$

$$
= \frac{2}{7}
$$

Only Maran eats cendol:

$$
\frac{3}{5} - \frac{3}{7}
$$

$$
= \frac{6}{35}
$$

Probability that Zalifah or Maran eats cendol:

$$
P(Z \cup M) = P(Z) + P(M) - P(Z \cap M)
$$

$$
= \frac{5}{7} + \frac{3}{5} - \frac{3}{7}
$$

$$
= \frac{31}{35}
$$

### Common Mistakes & Exam Tips:
- Put the intersection value in the overlap first.
- Subtract the overlap to get “only” regions.
- The probability outside all events can be found by subtracting all inside regions from $1$.

## Concept: Tree Diagrams with Conditional Replacement
Some problems have special replacement rules depending on the first outcome.

**Key Rules / Methods:**
- Read the condition carefully.
- If the first item is replaced, the total number remains the same.
- If the first item is not replaced, the total number decreases.
- Different branches may have different second-stage probabilities.

### Worked Example:
A box contains $7$ red marbles, $5$ yellow marbles and $3$ blue marbles.

Two marbles are chosen one by one.

If the first marble is blue, it is returned to the box before the second marble is chosen.

If the first marble is not blue, it is not returned.

Find the probability of getting two marbles of different colours.

Total marbles:

$$
7 + 5 + 3 = 15
$$

Different colours are:

$$
(R,Y),\ (R,B),\ (Y,R),\ (Y,B),\ (B,R),\ (B,Y)
$$

Probability:

$$
P(\text{different colours}) =
\left(\frac{7}{15}\times\frac{5}{14}\right)
+
\left(\frac{7}{15}\times\frac{3}{14}\right)
$$

$$
+
\left(\frac{5}{15}\times\frac{7}{14}\right)
+
\left(\frac{5}{15}\times\frac{3}{14}\right)
$$

$$
+
\left(\frac{3}{15}\times\frac{7}{15}\right)
+
\left(\frac{3}{15}\times\frac{5}{15}\right)
$$

$$
= \frac{349}{525}
$$

Using complement method:

$$
P(\text{different colours}) = 1 - P(\text{same colours})
$$

$$
= 1 - \left[\left(\frac{7}{15}\times\frac{6}{14}\right)
+
\left(\frac{5}{15}\times\frac{4}{14}\right)
+
\left(\frac{3}{15}\times\frac{3}{15}\right)\right]
$$

$$
= \frac{349}{525}
$$

### Common Mistakes & Exam Tips:
- Conditional replacement means not every branch uses the same denominator.
- If blue is replaced, the second draw still has $15$ marbles.
- If red or yellow is not replaced, the second draw has $14$ marbles.
- Complement method is often easier for “different colours” or “same colours”.

## Concept: Expected Number of Times an Event Occurs
If an experiment is repeated many times, the expected number of times an event occurs can be calculated using probability.

**Key Rules / Methods:**

$$
\text{Expected number} = P(\text{event}) \times \text{number of trials}
$$

### Worked Example:
A fair dice is rolled twice. The experiment is carried out $540$ times.

Find the expected number of times at least one perfect square is obtained.

Perfect squares on a dice are:

$$
1,\ 4
$$

Therefore:

$$
P(K) = \frac{2}{6} = \frac{1}{3}
$$

Probability of not getting a perfect square:

$$
P(K') = \frac{2}{3}
$$

At least one perfect square:

$$
P(\text{at least one }K) = 1 - P(K',K')
$$

$$
= 1 - \left(\frac{2}{3} \times \frac{2}{3}\right)
$$

$$
= 1 - \frac{4}{9}
$$

$$
= \frac{5}{9}
$$

Expected number:

$$
\frac{5}{9} \times 540 = 300
$$

Therefore, at least one perfect square is expected to occur $300$ times.

### Common Mistakes & Exam Tips:
- Multiply the probability by the number of trials.
- “At least one” is often easier using complement.
- The expected number should match the context, such as number of times, families, or customers.

## Concept: Application of Probability of Combined Events
Probability of combined events can be used in real-life decision-making and risk analysis.

**Key Rules / Methods:**
- Identify whether the events are independent or dependent.
- Draw a tree diagram if the problem has stages.
- Use multiplication along branches.
- Use addition for alternative outcomes.
- Use complement if it makes the calculation easier.
- Multiply by total number of cases when estimating the expected number.

### Common Applications:
- Choosing items from boxes or bags.
- Predicting repeated trial outcomes.
- Estimating number of customers receiving prizes.
- Comparing risks.
- Making choices based on probability.

### Common Mistakes & Exam Tips:
- Do not assume events are independent without checking the context.
- Look for keywords such as “with replacement”, “without replacement”, “at least”, “only”, “or”, and “and”.
- For staged problems, tree diagrams help reduce mistakes.
- For repeated trials, check whether probabilities stay the same each time.

## Concept: Summary of Key Probability Rules
The main probability rules in this topic are:

### Number of Combined Outcomes

$$
n(S) = n(A) \times n(B)
$$

### Probability of an Event

$$
P(A) = \frac{n(A)}{n(S)}
$$

### Complement Rule

$$
P(A') = 1 - P(A)
$$

### Multiplication Rule

For independent events:

$$
P(A \cap B) = P(A) \times P(B)
$$

### Addition Rule for Mutually Exclusive Events

If:

$$
A \cap B = \varnothing
$$

then:

$$
P(A \cup B) = P(A) + P(B)
$$

### Addition Rule for Non-Mutually Exclusive Events

If:

$$
A \cap B \neq \varnothing
$$

then:

$$
P(A \cup B) = P(A) + P(B) - P(A \cap B)
$$

### Expected Number

$$
\text{Expected number} = P(\text{event}) \times \text{number of trials}
$$

### Common Mistakes & Exam Tips:
- Use multiplication for “and”.
- Use addition rule for “or”.
- Subtract overlap for non-mutually exclusive events.
- Update probabilities for dependent events.
- Use complement for “at least one” when suitable.