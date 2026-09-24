# Topic: Network in Graph Theory
**Form:** Form 4 | **Chapter:** Chapter 5 | **Curriculum:** SPM KSSM

## Overview
Network in graph theory is used to represent relationships between objects using vertices and edges. In this topic, students learn about graphs, networks, vertices, edges, degrees, simple graphs, loops, multiple edges, directed graphs, undirected graphs, weighted graphs, unweighted graphs, subgraphs, trees, and solving problems involving networks.

## Concept: Graph and Network
A graph is used to represent discrete objects and the relationships between them in a simple visual form.

**Key Rules / Methods:**
- A graph consists of dots and lines.
- Each dot is called a vertex.
- Each line joining two vertices is called an edge.
- A graph is often used to represent a network.
- A network is part of a graph where the vertices and edges have specific meanings.
- Network data usually has a many-to-many relationship.

### Examples of Networks:
| Network | Vertices | Edges |
|---|---|---|
| Land transport network | Towns, cities, buildings, stations | Roads, highways, railway lines |
| Social network | Individuals, groups, organisations | Relationships such as friends, colleagues, family |
| Computer network | Computers and devices | Connections between devices |
| Flight network | Airports | Flight routes |

### Common Mistakes & Exam Tips:
- A vertex is a point or dot.
- An edge is a line or arc connecting vertices.
- A network is represented using a graph, but the vertices and edges must have real meanings.

## Concept: Graph Notation
A graph can be written using a set of vertices and a set of edges.

**Key Rules / Methods:**
- A graph is denoted as:

$$
G = (V, E)
$$

- $V$ is the set of vertices.
- $E$ is the set of edges.
- The set of vertices can be written as:

$$
V = \{v_1, v_2, v_3, \ldots, v_n\}
$$

- The set of edges can be written as:

$$
E = \{e_1, e_2, e_3, \ldots, e_n\}
$$

or as vertex pairs:

$$
E = \{(a_1, b_1), (a_2, b_2), \ldots, (a_n, b_n)\}
$$

- $n(V)$ means the number of vertices.
- $n(E)$ means the number of edges.

### Common Mistakes & Exam Tips:
- $V$ is the set of vertices, not the number of vertices.
- $n(V)$ is the number of vertices.
- $E$ is the set of edges, not the number of edges.
- $n(E)$ is the number of edges.

## Concept: Degree of a Vertex
The degree of a vertex is the number of edges connected to that vertex.

**Key Rules / Methods:**
- The degree of a vertex $v$ is written as:

$$
d(v)
$$

- The sum of degrees of a graph is twice the number of edges:

$$
\sum d(v) = 2n(E)
$$

where $v \in V$.

- If the graph has $7$ edges, then:

$$
\sum d(v) = 2(7) = 14
$$

### Worked Example:
Based on a simple graph with:

$$
V = \{1, 2, 3, 4, 5, 6\}
$$

and

$$
E = \{(1,2), (1,5), (2,3), (2,4), (3,4), (4,5), (5,6)\}
$$

Find $n(V)$, $n(E)$, and the sum of degrees.

Number of vertices:

$$
n(V) = 6
$$

Number of edges:

$$
n(E) = 7
$$

Sum of degrees:

$$
\sum d(v) = 2n(E)
$$

$$
= 2(7)
$$

$$
= 14
$$

### Common Mistakes & Exam Tips:
- Count every edge connected to the vertex.
- The total degree must be an even number.
- If the sum of degrees is odd, the graph cannot be drawn.
- For an undirected edge, the vertex pair $(1,2)$ is the same as $(2,1)$.

## Concept: Simple Graph
A simple graph is a graph with no loops and no multiple edges.

**Key Rules / Methods:**
- A simple graph has no loops.
- A simple graph has no multiple edges.
- The sum of degrees is twice the number of edges:

$$
\sum d(v) = 2n(E)
$$

### Worked Example:
Determine whether a graph with vertex degrees $3, 2, 2, 1, 3$ can be drawn.

Find the sum of degrees:

$$
3 + 2 + 2 + 1 + 3 = 11
$$

Since $11$ is odd, the graph cannot be drawn.

### Worked Example:
Determine whether a graph with vertex degrees $2, 1, 1, 3, 3, 2$ can be drawn.

Find the sum of degrees:

$$
2 + 1 + 1 + 3 + 3 + 2 = 12
$$

Since $12$ is even, the graph can be drawn.

### Common Mistakes & Exam Tips:
- A simple graph cannot have a loop.
- A simple graph cannot have two or more edges connecting the same pair of vertices.
- A graph cannot be drawn if the sum of degrees is odd.

## Concept: Multiple Edges
Multiple edges occur when the same pair of vertices is connected by more than one edge.

**Key Rules / Methods:**
- Multiple edges involve two vertices.
- The same two vertices are connected by more than one edge.
- Multiple edges are counted separately.
- The vertex pairs may be repeated, such as:

$$
(A,B), (A,B)
$$

### Common Mistakes & Exam Tips:
- If two vertices are connected by two different edges, count both edges.
- Multiple edges are not allowed in a simple graph.
- Repeated vertex pairs in $E$ indicate multiple edges.

## Concept: Loops
A loop is an edge that starts and ends at the same vertex.

**Key Rules / Methods:**
- A loop involves one vertex.
- A loop is written as a vertex pair with the same vertex repeated:

$$
(A,A)
$$

- In an undirected graph, each loop adds $2$ to the degree of the vertex.
- A loop is not allowed in a simple graph.

### Worked Example:
If vertex $S$ has one loop and two other edges connected to it, then:

$$
d(S) = 2 + 2 = 4
$$

The loop contributes $2$, and the two other edges contribute $1$ each.

### Common Mistakes & Exam Tips:
- A loop contributes $2$ to the degree in an undirected graph.
- Do not count a loop as only $1$ when finding the degree.
- A loop is written as $(A,A)$.

## Concept: Graph with Loops and Multiple Edges
Some graphs may contain loops and multiple edges.

**Key Rules / Methods:**
- A graph with loops and multiple edges is not a simple graph.
- Multiple edges are counted separately.
- Loops are counted as edges.
- For degree calculation, each loop adds $2$ to the degree.

### Worked Example:
The graph has:

$$
V = \{P, Q, R, S, T, U\}
$$

and

$$
E = \{(P,Q), (P,U), (P,U), (Q,R), (Q,U), (R,S), (R,T), (S,S), (S,T), (T,U)\}
$$

Find $n(V)$, $n(E)$, and the sum of degrees.

Number of vertices:

$$
n(V) = 6
$$

Number of edges:

$$
n(E) = 10
$$

Using the formula:

$$
\sum d(v) = 2n(E)
$$

$$
= 2(10)
$$

$$
= 20
$$

Therefore, the sum of degrees is $20$.

### Common Mistakes & Exam Tips:
- Count repeated edges separately.
- Count loops as edges.
- For degree, each loop contributes $2$.

## Concept: Directed Graph
A directed graph is a graph where each edge has a direction.

**Key Rules / Methods:**
- A directed graph uses arrows.
- Each directed edge has an initial vertex and a terminal vertex.
- The order of the vertices in an ordered pair matters.
- In a directed graph, $(A,B)$ means the edge goes from $A$ to $B$.
- $(A,B)$ and $(B,A)$ are different directed edges.
- Directed graphs are used to represent flows or processes.

### Examples of Directed Graphs:
- One-way road systems
- Flight routes
- Blood circulation
- Computer networks
- Organisation charts
- Electrical circuits

### Common Mistakes & Exam Tips:
- Pay attention to the arrow direction.
- In directed graphs, the order of the vertex pair matters.
- Do not treat $(A,B)$ and $(B,A)$ as the same edge.

## Concept: Undirected Graph
An undirected graph is a graph where the edges have no direction.

**Key Rules / Methods:**
- An undirected graph has no arrows.
- The order of the vertices in a vertex pair does not matter.
- In an undirected graph, $(A,B)$ and $(B,A)$ represent the same edge.
- An undirected graph can be simple or can have loops and multiple edges.

### Common Mistakes & Exam Tips:
- Do not assign direction to an undirected edge.
- For undirected graphs, $(A,B)$ is the same as $(B,A)$.
- If the graph has no arrows, it is undirected.

## Concept: In-Degree and Out-Degree in Directed Graphs
In a directed graph, the degree of a vertex can be separated into in-degree and out-degree.

**Key Rules / Methods:**
- In-degree means the number of edges going into a vertex.
- Out-degree means the number of edges going out from a vertex.
- The in-degree of vertex $A$ is written as:

$$
d_{\text{in}}(A)
$$

- The out-degree of vertex $A$ is written as:

$$
d_{\text{out}}(A)
$$

- The total degree of vertex $A$ is:

$$
d(A) = d_{\text{in}}(A) + d_{\text{out}}(A)
$$

### Worked Example:
If vertex $A$ has $2$ arrows going into it and $0$ arrows going out from it, then:

$$
d_{\text{in}}(A) = 2
$$

$$
d_{\text{out}}(A) = 0
$$

$$
d(A) = 2 + 0 = 2
$$

### Common Mistakes & Exam Tips:
- Arrows pointing into the vertex are counted as in-degree.
- Arrows pointing away from the vertex are counted as out-degree.
- A directed loop contributes to both in-degree and out-degree.

## Concept: Weighted Graph
A weighted graph is a graph where each edge has a value or weight.

**Key Rules / Methods:**
- A weighted graph can be directed or undirected.
- Each edge has a value called a weight.
- The weight may represent:
  - Distance
  - Travelling time
  - Cost
  - Current in an electrical circuit

### Worked Example:
If a route from $A$ to $B$ has weight $12$ km, and a route from $B$ to $C$ has weight $8$ km, then the total distance from $A$ to $C$ through $B$ is:

$$
12 + 8 = 20\text{ km}
$$

### Common Mistakes & Exam Tips:
- Weight is not the same as degree.
- The weight is written on the edge.
- In transportation networks, weights often represent distance, time, or cost.

## Concept: Unweighted Graph
An unweighted graph is a graph where the edges do not have values or weights.

**Key Rules / Methods:**
- An unweighted graph can be directed or undirected.
- Edges show relationships only.
- Edges do not show distance, cost, time, or other values.

### Examples of Unweighted Graphs:
- Organisation chart
- Flow map
- Tree map
- Bubble map
- Relationship map

### Common Mistakes & Exam Tips:
- If no value is assigned to the edge, the graph is unweighted.
- An unweighted graph still shows connections.
- Do not calculate total weight if there are no edge weights.

## Concept: Path and Distance in a Directed Weighted Graph
A directed weighted graph can be used to find routes, shortest distance, longest distance, or routes within a given range.

**Key Rules / Methods:**
- Follow the direction of arrows.
- Add the weights along the route.
- Compare total weights to find the shortest or longest route.
- A route is valid only if all arrows are followed in the correct direction.

### Worked Example:
A directed weighted graph shows one-way paths from $v_1$ to $v_5$.

Shortest route:

$$
v_1 \rightarrow v_2 \rightarrow v_5
$$

Distance:

$$
600 + 500 = 1100\text{ m}
$$

$$
= 1.1\text{ km}
$$

Longest route:

$$
v_1 \rightarrow v_2 \rightarrow v_3 \rightarrow v_4 \rightarrow v_5
$$

Distance:

$$
600 + 900 + 500 + 500 = 2500\text{ m}
$$

$$
= 2.5\text{ km}
$$

Routes with distance between $1.4$ km and $2.1$ km include:

$$
v_1 \rightarrow v_3 \rightarrow v_4 \rightarrow v_5
$$

and

$$
v_1 \rightarrow v_2 \rightarrow v_4 \rightarrow v_5
$$

### Common Mistakes & Exam Tips:
- Do not travel against the arrow direction.
- Convert metres to kilometres correctly.
- Compare total route distance, not individual edge distance only.
- A shortest route is not always the route with the fewest vertices.

## Concept: Subgraph
A subgraph is part of a graph, or the whole graph, redrawn without changing the original positions of the vertices and edges.

**Key Rules / Methods:**
A graph $H$ is a subgraph of graph $G$ if:
- The vertex set of $H$ is a subset of the vertex set of $G$:

$$
V(H) \subset V(G)
$$

- The edge set of $H$ is a subset of the edge set of $G$:

$$
E(H) \subset E(G)
$$

- The vertex pairs of the edges in $H$ are the same as the corresponding edges in $G$.

**Important Ideas:**
- A single vertex in graph $G$ is a subgraph of $G$.
- An edge in graph $G$ together with the vertices it connects is a subgraph of $G$.
- Every graph is a subgraph of itself.

### Worked Example:
If graph $G$ contains vertices:

$$
V(G) = \{P, Q, R, S\}
$$

and edges:

$$
E(G) = \{e_1, e_2, e_3, e_4, e_5\}
$$

A graph containing only edge $e_5$ joining vertices $P$ and $S$ is a subgraph because:

$$
\{e_5\} \subset \{e_1, e_2, e_3, e_4, e_5\}
$$

and

$$
\{P,S\} \subset \{P,Q,R,S\}
$$

### Common Mistakes & Exam Tips:
- A subgraph cannot invent a new edge that is not in the original graph.
- The position of a loop must remain on the same vertex.
- The edge must connect the same pair of vertices as in the original graph.
- Do not change the original structure when redrawing a subgraph.

## Concept: Tree
A tree is a special type of subgraph.

**Key Rules / Methods:**
A tree has the following properties:
- It is a simple graph.
- It has no loops.
- It has no multiple edges.
- All vertices are connected.
- Each pair of vertices is connected by only one path.
- If the tree has $n$ vertices, then the number of edges is:

$$
n - 1
$$

Therefore:

$$
\text{Number of edges} = \text{Number of vertices} - 1
$$

### Worked Example:
Determine whether a graph with $5$ vertices and $4$ edges can be a tree.

For a tree:

$$
\text{Number of edges} = n - 1
$$

$$
= 5 - 1
$$

$$
= 4
$$

Since the graph has $5$ vertices and $4$ edges, it can be a tree if all vertices are connected and there are no loops or multiple edges.

### Worked Example:
Determine whether a graph with $5$ vertices and $5$ edges is a tree.

For a tree with $5$ vertices:

$$
\text{Number of edges} = 5 - 1 = 4
$$

Since the graph has $5$ edges, it is not a tree.

### Common Mistakes & Exam Tips:
- A tree with $n$ vertices must have $n - 1$ edges.
- A tree must be connected.
- A tree cannot have loops or multiple edges.
- If there is more than one path between two vertices, it is not a tree.

## Concept: Drawing a Tree
A tree can be drawn when the number of vertices or edges is given.

**Key Rules / Methods:**
- If the number of vertices is given as $n$, then the number of edges is:

$$
n - 1
$$

- If the number of edges is given as $m$, then the number of vertices is:

$$
m + 1
$$

### Worked Example:
Draw a tree with $6$ vertices.

A tree with $6$ vertices has:

$$
6 - 1 = 5
$$

edges.

### Worked Example:
Draw a tree with $4$ edges.

A tree with $4$ edges has:

$$
4 + 1 = 5
$$

vertices.

### Common Mistakes & Exam Tips:
- Do not draw extra edges because that may create a cycle.
- Make sure all vertices are connected.
- Do not draw a loop or multiple edge in a tree.

## Concept: Minimum Total Weight Tree
A minimum total weight tree is a tree formed from a weighted graph with the smallest possible total weight while connecting all vertices.

**Key Rules / Methods:**
- The tree must include all vertices.
- The tree must be connected.
- The tree must not contain loops or cycles.
- If there are $n$ vertices, the tree must have $n - 1$ edges.
- Choose edges with smaller weights while keeping all vertices connected.
- Remove unnecessary larger edges if they create cycles.

### Worked Example:
An undirected weighted graph has $5$ vertices and $7$ edges.

Since a tree with $5$ vertices needs:

$$
5 - 1 = 4
$$

edges, remove $3$ edges.

Suppose the selected edge weights are:

$$
10,\ 12,\ 14,\ 19
$$

Minimum total weight:

$$
10 + 12 + 14 + 19 = 55
$$

Therefore, the minimum total weight of the tree is $55$.

### Common Mistakes & Exam Tips:
- Do not choose only the smallest edges if they do not connect all vertices.
- The final graph must be a tree.
- Check that all vertices are connected.
- Check that the number of edges is $n - 1$.
- Avoid cycles.

## Concept: Representing Information as Networks
Information can be represented in the form of networks using vertices and edges.

**Key Rules / Methods:**
- Choose what the vertices represent.
- Choose what the edges represent.
- If edge values are needed, use a weighted graph.
- If directions are needed, use a directed graph.
- If directions are not needed, use an undirected graph.
- If repeated relationships occur, multiple edges may be used.

### Examples:
| Situation | Vertices | Edges |
|---|---|---|
| Train transit map | Stations | Train lines |
| Road map | Places | Roads |
| Social relationship | People | Relationships |
| Pupils and games | Games or pupils | Pupils’ choices or shared activities |
| Maze | Junctions or turning points | Paths |

### Worked Example:
A table shows pupils and the games they like.

| Pupil | Games |
|---|---|
| Edmund | Badminton, Chess |
| Azwan | Football, Sepak takraw |
| Rajan | Chess, Football |
| Aina | Chess, Netball |
| Maria | Badminton, Netball |
| Jenny | Netball, Volleyball |

One way to represent the information:
- Let the vertices represent the types of games.
- Let the edges represent the pupils’ names.

For example:
- Edmund connects Badminton and Chess.
- Rajan connects Chess and Football.
- Maria connects Badminton and Netball.

### Common Mistakes & Exam Tips:
- Choose vertices that are not repeated too much.
- Edges should represent the relationship between vertices.
- For networks involving distance or cost, use a weighted graph.
- For networks involving one-way movement, use a directed graph.

## Concept: Solving Problems Involving Networks
Network problems may involve choosing routes based on cost, time, distance, or practical conditions.

**Key Rules / Methods:**
- Identify the vertices and edges.
- Identify whether the graph is directed or undirected.
- Identify whether the graph is weighted or unweighted.
- For route problems, add the relevant weights.
- Compare the routes based on what the question asks:
  - Shortest distance
  - Lowest cost
  - Shortest time
  - Most practical route
- Justify the answer based on the situation.

### Worked Example:
A journey from Johor Bahru to Kota Bharu can be made by bus, train, or cab.

If an adult has no time constraint, taking a train with bed may be suitable because the passenger can rest throughout the journey and the price difference compared to a train without bed is small.

If an adult has a time constraint, taking a bus may be suitable because the journey is shorter than by train and cheaper than a cab.

If two adults and two children travel together, taking a cab may be the most economical choice because the cab cost is shared.

### Worked Example:
For a flight route from Kuala Lumpur to Kota Kinabalu, the direct flight is usually the best route because it saves time and cost compared to a route with transit.

### Common Mistakes & Exam Tips:
- The shortest distance is not always the shortest time.
- The cheapest route is not always the most practical route.
- For weighted graphs, check what the weight represents before comparing.
- Always justify the answer using the condition in the question.