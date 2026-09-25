## Topic Coverage Instruction
Strictly flow this protocol and as a checklist for each concept topic, tool, tech.
When teaching any topic, cover it **completely and systematically**, from fundamentals to advanced/production level.

Follow this structure:

1. **Overview & Purpose**

   * What is it?
   * Why does it exist?
   * What problem does it solve?
   * Where is it used?
   * Where does it fit in backend/software engineering?

2. **Prerequisites**

   * Explain only the concepts required to understand the topic.
   * Do not assume important prerequisites.

3. **Complete Theory**

   * Cover all major concepts, sub-concepts, terminology, principles, patterns, and important edge cases.
   * Do not skip foundational concepts or important advanced concepts.
   * Explain every technical term in simple language first, followed by the precise engineering meaning.

4. **Theory + Example**

   * For every major theoretical concept, immediately give a small concrete example.
   * Whenever possible, include a **simple code example directly inside the theoretical explanation**.
   * Do not separate theory and practice too far apart.

5. **Visual Explanation**

   * Use diagrams wherever they improve understanding.
   * Prefer arch diagrams for(check few examples in systemDesign module):

     * architecture
     * data flow
     * request flow
     * lifecycle
     * component relationships
     * sequence of operations
     * failure scenarios
   * Explain every diagram.

6. **How It Works Internally**

   * Explain the internal mechanism and execution flow to the depth relevant for a backend engineer.
   * Explain what happens step-by-step rather than only showing how to use the tool/API.

7. **Real-World Engineering Usage**

   * Show how the topic is actually used in real backend/production systems.
   * Explain common architectural patterns, trade-offs, limitations, and mistakes.

8. **Failure & Debugging**

   * Explain common failure modes.
   * Show what the failure looks like.
   * Explain how an engineer would diagnose and fix it.
   * Include practical debugging examples.

9. **Production Concerns**
   Cover relevant:

   * reliability
   * security
   * performance
   * scalability
   * observability
   * deployment/operations
   * failure recovery
   * trade-offs

10. **Practical Projects — Exactly 5 in Go**
    Create five progressively difficult projects:

    * Project 1: very basic, focused on understanding the core mechanism
    * Project 2: basic real-world backend use case
    * Project 3: intermediate multi-component system
    * Project 4: advanced production-oriented system
    * Project 5: realistic advanced/production-style project

11. **Practical Projects — Exactly 5 in Python**
    Create five progressively difficult projects using the same progression:

    * Project 1: very basic
    * Project 2: basic real-world
    * Project 3: intermediate
    * Project 4: advanced production-oriented
    * Project 5: realistic advanced/production-style project

12. **Project Requirements**
    Every project must include, where relevant:

    * problem statement
    * architecture diagram
    * project structure
    * complete runnable code
    * setup instructions
    * configuration
    * dependencies
    * tests
    * expected behavior/output
    * failure scenarios
    * debugging
    * production considerations
    * explanation of important design decisions

13. **Progressive Difficulty**
    Do not introduce advanced concepts too early.

    Progress as:

    `Fundamentals → Simple Example → Basic Project → Intermediate → Advanced → Production Project`

14. **Interview Preparation**
    After the topic is covered, include interview-oriented material:

    * fundamental questions
    * practical questions
    * debugging questions
    * design/trade-off questions
    * advanced/backend questions
    * system-design questions where relevant
    * common misconceptions/interviewer follow-ups

15. **Final Summary**
    End with:

    * key mental models
    * important terminology
    * cheat sheet
    * common mistakes
    * production checklist
    * interview checklist

### Quality Rule

Do not give a shallow tutorial or a list of definitions.

The topic should be covered so that I can:

**understand it → implement it → use it in a backend → debug it → reason about production behavior → design with it → explain it in an interview.**

For every major concept, follow:

**Theory → Simple Example → Diagram (when useful) → Practical Usage → Production Considerations → Interview Perspective.**
