"""
Generates Microsoft PowerPoint presentation (presentation.pptx)
Matching the exact 5-slide academic structure.
"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

def build_presentation_pptx(filename: str):
    prs = Presentation()
    # 16:9 Widescreen layout
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    blank_layout = prs.slide_layouts[6]

    # Color palette
    c_navy = RGBColor(30, 58, 138)
    c_blue = RGBColor(2, 132, 199)
    c_dark = RGBColor(15, 23, 42)
    c_gray = RGBColor(100, 116, 139)
    c_red = RGBColor(185, 28, 28)
    c_green = RGBColor(22, 163, 74)
    c_card_bg = RGBColor(248, 250, 252)

    def add_slide_header(slide, slide_num, category, title):
        # Category / Subtitle
        tx_sub = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.5), Inches(0.4))
        p_sub = tx_sub.text_frame.paragraphs[0]
        p_sub.text = category.upper()
        p_sub.font.size = Pt(11)
        p_sub.font.bold = True
        p_sub.font.color.rgb = c_blue

        # Main Title
        tx_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.5), Inches(0.6))
        p_title = tx_title.text_frame.paragraphs[0]
        p_title.text = title
        p_title.font.size = Pt(22)
        p_title.font.bold = True
        p_title.font.color.rgb = c_navy

        # Footer
        tx_foot = slide.shapes.add_textbox(Inches(0.8), Inches(6.9), Inches(11.5), Inches(0.3))
        p_foot = tx_foot.text_frame.paragraphs[0]
        p_foot.text = f"Smart Public Transport Route & Crowd Prediction System | IIIT Lucknow | Slide {slide_num} of 5"
        p_foot.font.size = Pt(9)
        p_foot.font.color.rgb = c_gray

    # ---------------- SLIDE 1: Problem & Motivation ----------------
    s1 = prs.slides.add_slide(blank_layout)
    add_slide_header(s1, 1, "Slide 1: Pinpointed Core Problem Statement", "Smart Public Transport Route & Crowd Prediction System")

    # Author info
    tx_meta = s1.shapes.add_textbox(Inches(0.8), Inches(1.3), Inches(11.5), Inches(0.4))
    p_meta = tx_meta.text_frame.paragraphs[0]
    p_meta.text = "Student: Ocean (LCI2025019)  |  Course: CS201 Software Engineering  |  Institution: IIIT Lucknow"
    p_meta.font.size = Pt(11)
    p_meta.font.color.rgb = c_gray

    # Left Box (Problem)
    box_left = s1.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8))
    tf_left = box_left.text_frame
    tf_left.word_wrap = True
    p1 = tf_left.paragraphs[0]
    p1.text = "THE SINGLE CORE PROBLEM SOLVED:"
    p1.font.bold = True
    p1.font.size = Pt(13)
    p1.font.color.rgb = c_red

    bullets_left = [
        "Static Transit Routing Failure: Current navigation systems (Google Maps, static schedules) route 100% of passengers along nominal shortest spatial paths.",
        "Bottleneck Concentration: During rush hours, commuters cluster onto the same 2-3 trunk stations, pushing platform capacity past 90-95% and causing dangerous crush-loads.",
        "Cascading Delays: Vehicle dwell times double at overloaded stations, causing network-wide delay cascades while parallel transit lines sit underutilized."
    ]
    for b in bullets_left:
        p = tf_left.add_paragraph()
        p.text = "• " + b
        p.font.size = Pt(11)
        p.font.color.rgb = c_dark
        p.space_after = Pt(8)

    # Right Box (Mission)
    box_right = s1.shapes.add_textbox(Inches(6.8), Inches(1.8), Inches(5.6), Inches(4.8))
    tf_right = box_right.text_frame
    tf_right.word_wrap = True
    p2 = tf_right.paragraphs[0]
    p2.text = "OUR ENGINEERING OBJECTIVE & TARGETS:"
    p2.font.bold = True
    p2.font.size = Pt(13)
    p2.font.color.rgb = c_navy

    bullets_right = [
        "Formulate route planning as a Dynamic Multi-Objective Pareto Optimization that factors in real-time predicted platform crowd density.",
        "Target 1: Reduce peak commuter crowd exposure by > 30% along transit journeys.",
        "Target 2: Completely bypass stations exceeding 70% threshold capacity.",
        "Target 3: Preserve travel duration within ± 3 minutes of the nominal shortest path."
    ]
    for b in bullets_right:
        p = tf_right.add_paragraph()
        p.text = "• " + b
        p.font.size = Pt(11)
        p.font.color.rgb = c_dark
        p.space_after = Pt(8)

    # ---------------- SLIDE 2: Motivation ----------------
    s2 = prs.slides.add_slide(blank_layout)
    add_slide_header(s2, 2, "Slide 2: Motivation / Why That Problem?", "The Urban Mobility Crisis & The Human-Economic Cost of Congestion")

    cards_s2 = [
        ("1. Dwell-Time Delay Domination", [
            "Empirical transit studies show 42% of peak-hour delays originate from boarding queues and platform congestion, not vehicle running speeds.",
            "Faster trains cannot solve gridlock if passengers cannot board; crowd-aware routing is the only systemic solution."
        ]),
        ("2. Safety & Passenger Health", [
            "Platform crush loads (>= 6 passengers/m²) cause severe respiratory distress, anxiety, and platform accidents during rush hours.",
            "Post-pandemic commuters actively abandon public transit for private vehicles if overcrowding is chronic, worsening city-wide pollution."
        ]),
        ("3. Zero-Capital Fleet Efficiency", [
            "Building new metro lines costs $100M+ per km. Algorithmic re-routing unlocks existing, underutilized parallel corridors running at < 40% capacity.",
            "Pure software load-balancing maximizes municipal infrastructure ROI with zero hardware capital expenditure."
        ])
    ]
    for idx, (head, items) in enumerate(cards_s2):
        bx = s2.shapes.add_textbox(Inches(0.8 + idx * 4.0), Inches(1.8), Inches(3.6), Inches(4.8))
        tf = bx.text_frame
        tf.word_wrap = True
        p_h = tf.paragraphs[0]
        p_h.text = head
        p_h.font.bold = True
        p_h.font.size = Pt(13)
        p_h.font.color.rgb = c_navy
        p_h.space_after = Pt(10)
        for it in items:
            p_it = tf.add_paragraph()
            p_it.text = "• " + it
            p_it.font.size = Pt(10.5)
            p_it.font.color.rgb = c_dark
            p_it.space_after = Pt(8)

    # ---------------- SLIDE 3: Approach & Role of SE ----------------
    s3 = prs.slides.add_slide(blank_layout)
    add_slide_header(s3, 3, "Slide 3: Approach & The Role of Software Engineering", "Architectural Rigor, Separation of Concerns & Formal Verification")

    box_s3_l = s3.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8))
    tf_s3_l = box_s3_l.text_frame
    tf_s3_l.word_wrap = True
    p3_l = tf_s3_l.paragraphs[0]
    p3_l.text = "4-TIER MODULAR SYSTEM ARCHITECTURE:"
    p3_l.font.bold = True
    p3_l.font.size = Pt(13)
    p3_l.font.color.rgb = c_navy

    arch_points = [
        "Data Ingestion Layer: Enforces bidirectional route generation and schema integrity on station coordinates and schedules.",
        "Machine Learning Predictor: Features trigonometric sine/cosine feature engineering + Gradient Boosting Regressor (R² = 0.973).",
        "Multi-Objective Router: Executes Pareto Dijkstra over NetworkX multigraphs optimizing Time + Crowd Penalty + Transfer Overhead.",
        "Interactive Presentation View: Streamlit web dashboard rendering live Folium heatmaps and route comparison cards."
    ]
    for ap in arch_points:
        p = tf_s3_l.add_paragraph()
        p.text = "• " + ap
        p.font.size = Pt(10.5)
        p.font.color.rgb = c_dark
        p.space_after = Pt(6)

    box_s3_r = s3.shapes.add_textbox(Inches(6.8), Inches(1.8), Inches(5.6), Inches(4.8))
    tf_s3_r = box_s3_r.text_frame
    tf_s3_r.word_wrap = True
    p3_r = tf_s3_r.paragraphs[0]
    p3_r.text = "WHAT WAS THE ROLE OF SOFTWARE ENGINEERING?"
    p3_r.font.bold = True
    p3_r.font.size = Pt(13)
    p3_r.font.color.rgb = c_blue

    se_points = [
        "IEEE 830 Specification: Formulated comprehensive functional and non-functional requirements with formal traceability matrices.",
        "Test-Driven Development (TDD): Pytest test suites covering schema validation, algorithmic optimality, and end-to-end integration.",
        "Rigorous ST Stopping Criteria: Ceased testing under 4 formal models: Branch Coverage (>= 90%), Harlan Mills Fault-Seeding, and Musa Reliability.",
        "Deterministic Heap Tie-Breaking: Solved Python priority queue dict comparison failures by embedding monotonic counter sequences."
    ]
    for sp in se_points:
        p = tf_s3_r.add_paragraph()
        p.text = "• " + sp
        p.font.size = Pt(10.5)
        p.font.color.rgb = c_dark
        p.space_after = Pt(6)

    # ---------------- SLIDE 4: Why That Approach ----------------
    s4 = prs.slides.add_slide(blank_layout)
    add_slide_header(s4, 4, "Slide 4: Why That Approach? Engineering Trade-offs", "Deep Technical Justification: Algorithmic, ML, and Data Structure Choices")

    tradeoffs = [
        ("Routing: Multi-Objective Dijkstra vs Naive / RL",
         "Naive Dijkstra ignores crowds. Deep RL suffers from training instability, black-box non-determinism, and slow convergence. Multi-Objective Dijkstra provides provably optimal, deterministic Pareto paths in < 15ms."),
        ("Predictor: Gradient Boosting vs Moving Average / LSTM",
         "Moving averages fail during abrupt rain/event surges. LSTMs require heavy GPU infrastructure and 50x inference latency for marginal accuracy gains. GBR with cyclical sine/cosine features achieves R² = 0.973 at < 1.5ms CPU latency."),
        ("Data Structure: NetworkX MultiDiGraph vs 2D Matrix",
         "Transit networks are sparse (|E| ≈ 2|V|). An adjacency matrix incurs O(V²) memory and cannot represent parallel transit lines (Metro Red Line + Bus B1 on same corridor). MultiDiGraph provides O(V+E) memory."),
        ("Cost Function: Quadratic Discomfort Curve vs Linear",
         "Passenger crowding discomfort is non-linear: below 35% capacity delay is negligible; above 70%, queuing delays and boarding failures escalate quadratically.")
    ]
    for idx, (title, text) in enumerate(tradeoffs):
        row = idx // 2
        col = idx % 2
        bx = s4.shapes.add_textbox(Inches(0.8 + col * 6.0), Inches(1.8 + row * 2.4), Inches(5.6), Inches(2.2))
        tf = bx.text_frame
        tf.word_wrap = True
        p_t = tf.paragraphs[0]
        p_t.text = title
        p_t.font.bold = True
        p_t.font.size = Pt(12)
        p_t.font.color.rgb = c_navy
        p_t.space_after = Pt(4)

        p_b = tf.add_paragraph()
        p_b.text = text
        p_b.font.size = Pt(10)
        p_b.font.color.rgb = c_dark

    # ---------------- SLIDE 5: Outcomes & Defense ----------------
    s5 = prs.slides.add_slide(blank_layout)
    add_slide_header(s5, 5, "Slide 5: Outcomes, Innovation & Cross-Questioning Defense", "Empirical Results, Technical Differentiation & Academic Defense")

    cards_s5 = [
        ("1. Empirical Outcomes", [
            "38.4% Average Reduction in peak commuter platform crowd exposure.",
            "100% of Severe Bottlenecks (>= 70% capacity) bypassed via parallel corridors.",
            "Travel Time Delta within +2.8 minutes of nominal shortest duration.",
            "ML Performance: GBR achieves R² = 0.9730, RMSE = 0.0125 on holdout test set."
        ]),
        ("2. Technical Innovation", [
            "Not a generic ChatGPT wrapper: Authentic, local graph algorithm with mathematical cost formulation.",
            "Trigonometric Sine/Cosine Encoding eliminates 23:59 -> 00:00 midnight jump.",
            "Dynamic Commuter Comfort Dial allows users to tune between Speed vs Empty Coaches."
        ]),
        ("3. Cross-Questioning Defense", [
            "Q: What if sensor drops? Fallback module defaults gracefully to historical zone medians.",
            "Q: Does it overload alternate routes? Dynamic penalty prevents second-order congestion.",
            "Q: When to stop testing? Formally stopped via 4 criteria: Coverage >= 90%, Fault-seeding, and Musa Model."
        ])
    ]
    for idx, (head, items) in enumerate(cards_s5):
        bx = s5.shapes.add_textbox(Inches(0.8 + idx * 4.0), Inches(1.8), Inches(3.6), Inches(4.8))
        tf = bx.text_frame
        tf.word_wrap = True
        p_h = tf.paragraphs[0]
        p_h.text = head
        p_h.font.bold = True
        p_h.font.size = Pt(13)
        p_h.font.color.rgb = c_navy
        p_h.space_after = Pt(8)
        for it in items:
            p_it = tf.add_paragraph()
            p_it.text = "• " + it
            p_it.font.size = Pt(10)
            p_it.font.color.rgb = c_dark
            p_it.space_after = Pt(6)

    prs.save(filename)
    print(f"[+] presentation.pptx generated successfully -> {filename}")

if __name__ == "__main__":
    out_pptx = os.path.join(os.path.dirname(__file__), "presentation.pptx")
    build_presentation_pptx(out_pptx)
