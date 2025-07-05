# Custom CSS styles for the title
title_style = """
    font-size: 4em;
    text-align: center;
    margin-bottom: 20px;
    font-family: 'Arial', sans-serif;
"""

# Render title with custom styling
def render_title(st):
    st.markdown(f"""
        <div style="{title_style}">
            <span style="color: #FF5733;">S</span>
            <span style="color: #C70039;">c</span>
            <span style="color: #900C3F;">i</span>
            <span style="color: #581845;">T</span>
            <span style="color: #900C3F;">r</span>
            <span style="color: #C70039;">u</span>
            <span style="color: #FFC300;">e</span>
            <span style="font-size: 0.7em; vertical-align: middle; margin-left: 10px;">📚</span>
        </div>
    """, unsafe_allow_html=True)

# Custom CSS styles for inputs and button
input_style = """
    padding: 10px;
    margin: 10px;
    border: 2px solid #800080;
    border-radius: 5px;
    font-size: 1.2em;
    width: 80%;
    box-sizing: border-box;
    font-family: 'Arial', sans-serif;
"""

button_style = """
    background-color: #800080;
    color: white;
    padding: 15px 30px;
    border: none;
    border-radius: 5px;
    font-size: 1.2em;
    cursor: pointer;
    font-family: 'Arial', sans-serif;
"""

# Render custom styles in Streamlit
def render_custom_styles(st):
    st.markdown(f"""
        <style>
            .styled-input {{
                {input_style}
            }}
            .styled-button {{
                {button_style}
            }}
        </style>
    """, unsafe_allow_html=True)

# Render accuracy score
def render_accuracy_score(accuracy_score: str) -> str:
    if '/' in accuracy_score:
        numerator, denominator = map(int, accuracy_score.split('/'))
        score = (numerator / denominator) * 100
    else:
        score = float(accuracy_score)
    
    if score >= 90:
        color = "#4CAF50"  # Green
    elif score > 65:
        color = "#FFC107"  # Orange
    else:
        color = "#F44336"  # Red
        
    return f"""
        <div style="padding: 10px; border: 2px solid {color}; border-radius: 5px; background-color: #f9f9f9; margin-bottom: 10px;">
            <h3 style="color: {color}; margin-top: 0;">Accuracy Score:</h3>
            <p style="font-size: 16px; color: #333;">{accuracy_score}</p>
        </div>
    """

# Render reason for accuracy
def render_reason_for_accuracy(reason: str, color: str) -> str:
    return f"""
        <div style="padding: 10px; border: 2px solid {color}; border-radius: 5px; background-color: #f9f9f9;">
            <h3 style="color: {color}; margin-top: 0;">Verdict and Reason:</h3>
            <p style="font-size: 16px; color: #333;">{reason}</p>
        </div>
    """

# Function to generate color based on index
def generate_color(index):
    colors = [
        '#F7B7B7',
        '#E6E6FA',
        '#FFEFD5',
        '#F0FFFF',
        '#FFFAFA',
        '#FFF0F5',
        '#F5F5DC',
        '#FFE4C4',
        '#E0FFFF'
    ]
    return colors[index % len(colors)]

def build_html_tree(data):
    key_display_names = {
        'journal_title': 'Journal Title',
        'authors': 'Authors',
        'venue': 'Venue',
        'year': 'Year',
        'abstract': 'Abstract',
        'section': 'Section',
        'paragraph': 'Paragraph',
        'title': 'Title',
        'claim': 'Claim',
        'url': 'URL',
        'relevant sentence': 'Relevant Sentence',
        'type': 'Type',
        'label': 'Label',
        'supporting assumptions': 'Supporting Assumptions',
        'refuting assumptions': 'Refuting Assumptions',
        "citationCount": 'Citation Count',
        'sjr': 'SJR',
        # 'relevant sentence type':"Relevant Sentence Type",
        # "function_reason":"Function of the Text Reason",
        # "relation":"Claim/Article Relation",
        # "relation_reason":"Claim/Article Relation Reason"
    }

    keys_hidden_by_default = {
        'paragraph': True,
        'supporting assumptions': True,
        'refuting assumptions': True,
        'abstract': True
    }

    contribution_colors = {
        'corroborating': '#1F4307',
        'partially corroborating': '#34740A',
        'slightly corroborating': '#42930D',
        'contrasting': '#931C0D',
        'partially contrasting': '#CB4231',
        'slightly contrasting': '#E15F50',
        'inconclusive': 'black'
    }

    # List of features to hide
    hidden_features = ['type', 'authors','journal_title','accuracy','reason for accuracy']

    def get_contribution_color(value):
        return contribution_colors.get(value.lower(), 'black')

    def create_node(item, idx):
        color = generate_color(idx)
        children_html = ""

        for key, value in item.items():
            # Skip features in the hidden list
            if key in hidden_features:
                continue

            if key == "contribution":
                continue

            if key == "section" and not value:
                continue

            if key == "supporting assumptions" and (not value or len(value) == 0):
                continue

            if key == "refuting assumptions" and (not value or len(value) == 0):
                continue

            display_name = key_display_names.get(key, key)

            hide_by_default = keys_hidden_by_default.get(key, False)

            # if key == 'contribution' and len(value) >= 2:
            #     contribution_color = get_contribution_color(value)
            #     children_html += f"<li style='background-color: {color}; color: {contribution_color};'><strong>{display_name}:</strong> {value}</li>"
            if key in ['accuracy', 'reason for accuracy'] and len(value) >= 2:
                children_html += f"<li style='background-color: {color};'><strong>{display_name}:</strong> {value}</li>"
            elif key in key_display_names:
                if key == 'url' and len(value) >= 2:
                    children_html += f"<li style='background-color: {color};'><strong>{display_name}:</strong> <a href='{value}' target='_blank'>{value}</a></li>"
                elif hide_by_default:
                    if isinstance(value, list):
                        formatted_value = "<ul style='margin:4px 0 0 16px; padding:0;'>"
                        formatted_value += "".join([f"<li>{item}</li>" for item in value])
                        formatted_value += "</ul>"
                    else:
                        formatted_value = value

                    children_html += f"""
                        <li style='background-color: {color}; padding:6px; border-radius:4px;'>
                            <strong>{display_name}:</strong>
                            <span class="caret-toggle" onclick="toggleContent(this)" style="cursor:pointer; color:#007bff; text-decoration:underline;">
                                Show {display_name}
                            </span>
                            <div class="content-hidden" style="display:none; margin-top:4px;">
                                {formatted_value}
                            </div>
                        </li>
                        """
                elif isinstance(value, dict):
                    dict_items_html = ""
                    for k, v in value.items():
                        if isinstance(v, str) and v.startswith("http"):
                            v_html = f"<a href='{v}' target='_blank'>{v}</a>"
                        else:
                            v_html = v
                        dict_items_html += f"<li><strong>{k}:</strong> {v_html}</li>"

                    formatted_value = f"""
                            <ul style='margin:4px 0 0 16px; padding:0;'>
                                {dict_items_html}
                            </ul>
                            """

                    children_html += f"""
                            <li style='background-color: {color}; padding:6px; border-radius:4px;'>
                                <strong>{display_name}:</strong>
                                <span class="caret-toggle" onclick="toggleContent(this)" style="cursor:pointer; color:#007bff; text-decoration:underline;">
                                    Show {display_name}
                                </span>
                                <div class="content-hidden" style="display:none; margin-top:4px;">
                                    {formatted_value}
                                </div>
                            </li>
                            """
                elif isinstance(value, list):
                    assumptions_html = ''.join([f"<li>{assumption}</li>" for assumption in value])
                    children_html += f"<li><strong>{display_name}:</strong><ul>{assumptions_html}</ul></li>"
                elif len(str(value)) >= 2:
                    children_html += f"<li style='background-color: {color};'><strong>{display_name}:</strong> {value}</li>"

        if item.get("relevant sentence type") and item.get("function_reason"):
            children_html += f"""
                        <li style='background-color: {color}; padding:6px; border-radius:4px;'>
                            <strong>Context:</strong>
                            <span class="caret-toggle" onclick="toggleContent(this)" style="cursor:pointer; color:#007bff; text-decoration:underline;">
                                Show Context
                            </span>
                            <div class="content-hidden" style="display:none; margin-top:4px;">
                                The source is highly likely contributing {item.get("relevant sentence type")} of the study. {item.get("function_reason")}
                            </div>
                        </li>
                        """

        if item.get("relation") and item.get("relation_reason"):
            children_html += f"""
                        <li style='background-color: {color}; padding:6px; border-radius:4px;'>
                            <strong>Claim/Article Relation:</strong>
                            <span class="caret-toggle" onclick="toggleContent(this)" style="cursor:pointer; color:#007bff; text-decoration:underline;">
                                Show Claim/Article Relation
                            </span>
                            <div class="content-hidden" style="display:none; margin-top:4px;">
                                The claim article relationship is {item.get("relation")}(strong/medium/weak) – {item.get("relation_reason")}                            
                            </div>
                        </li>
                        """

        contribution = item.get("contribution", "")
        contribution_color = get_contribution_color(contribution)

        return f"""
        <li>
            <span class="caret" style="background-color: {color};" onclick="toggleNested(this)">
                Subclaim {idx + 1}<span style="color: {contribution_color}; margin-left:8px; font-weight:600;">{contribution}</span>
            </span>
            <ul class="nested">
                {children_html} <br>
            </ul>
        </li>
        """

    if not isinstance(data, list):
        raise TypeError("Input data must be a list of dictionaries.")

    tree_html = """
    <style>
        .nested { display: none; }
        .active { display: block; }
        .caret::before { content: "\\25B6"; color: black; display: inline-block; margin-right: 6px; }
        .caret-down::before { content: "\\25BC"; color: black; display: inline-block; margin-right: 6px; }
        .caret-toggle { color: blue; cursor: pointer; text-decoration: underline; }
        .content-hidden { display: none; }
    </style>
    <ul id='myUL'>
    """
    for idx, item in enumerate(data):
        tree_html += create_node(item, idx)
    tree_html += "</ul>"
    tree_html += """
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            var togglers = document.getElementsByClassName('caret');
            for (var i = 0; i < togglers.length; i++) {
                togglers[i].addEventListener('click', function() {
                    this.parentElement.querySelector('.nested').classList.toggle('active');
                    this.classList.toggle('caret-down');
                });
            }
        });

        function toggleNested(element) {
            var content = element.parentElement.querySelector('.nested');
            content.classList.toggle('active');
            element.classList.toggle('caret-down');
        }

        function toggleContent(element) {
            var content = element.nextElementSibling;
            if (content.style.display === "none") {
                content.style.display = "block";
                element.textContent = "Hide " + element.textContent.split(" ")[1];
            } else {
                content.style.display = "none";
                element.textContent = "Show " + element.textContent.split(" ")[1];
            }
        }
    </script>
    """
    return tree_html

# HTML generation
def generate_html_code(html_tree):
    return f"""
    <style>
        ul, #myUL {{
            list-style-type: none;
            padding: 0;
            margin: 0;
            font-family: 'Roboto', sans-serif;
        }}
        #myUL {{
            background-color: #f9f9f9;
            border: 1px solid #bbb;
            padding: 5px;
            border-radius: 8px;
            max-width: 1200px;
            box-sizing: border-box;
            margin: auto;
        }}
        .caret {{
            cursor: pointer;
            user-select: none;
            color: #333;
            font-weight: bold;
            padding: 10px 15px;
            border-radius: 4px;
            transition: background-color 0.3s, color 0.3s;
            display: block;
            position: relative;
        }}
        .caret::before {{
            content: "\\25B6";
            color: #333;
            display: inline-block;
            margin-right: 10px;
            transition: transform 0.3s;
        }}
        .caret-down::before {{
            content: "\\25BC";
            transform: rotate(0deg);
        }}
        .nested {{
            display: none;
            margin-left: 20px;
            border-left: 2px dashed #007bff;
            padding-left: 10px;
            border-radius: 4px;
        }}
        .active {{
            display: block;
        }}
        .caret:hover {{
            background-color: #0056b3;
            color: white;
        }}
        li {{
            margin: 5px 0;
            padding: 5px;
            border-radius: 4px;
        }}
        li:hover {{
            background-color: #bbdefb;
        }}
    </style>

    <p style="text-align:center;">
    <button onclick="toggleTree()" style="padding: 15px 25px; background-color: #FF0000; color: white; border: none; border-radius: 10px; cursor: pointer; font-size: 18px;">Click to Show/Hide Details</button>
    </p>

    <div id="tree-container" style="display: none;">
        {html_tree}
    </div>
    <script>
        document.addEventListener("DOMContentLoaded", function() {{
            var toggler = document.getElementsByClassName("caret");
            resizeFrame(true);
            for (var i = 0; i < toggler.length; i++) {{
                toggler[i].addEventListener("click", function() {{
                    this.parentElement.querySelector(".nested").classList.toggle("active");
                    this.classList.toggle("caret-down");
                    resizeFrame(false);
                }});
            }}
        }});

        function toggleTree() {{
            var container = document.getElementById('tree-container');
            if (container.style.display === "none") {{
                container.style.display = "block";
                resizeFrame(false);
            }} else {{
                container.style.display = "none";
                resizeFrame(true);
            }}
        }}

        function resizeFrame(initial) {{
            var treeContainer = document.getElementById('tree-container');
            var newHeight = treeContainer.scrollHeight + 20; // Add some padding
            if(initial){{
                newHeight += 50;
            }}
            window.frameElement.style.height = newHeight + 'px';
        }}
    </script>
    """
def badge_label(label, bg='#8e44ad', color='#fff'):
    return f"""<span style='
        display:inline-block;
        font-size:17px;
        font-weight:bold;
        color:{color};
        background:{bg};
        padding:3px 12px;
        border-radius:10px;
        margin-right:10px;
        margin-bottom:6px;
        vertical-align:middle;
    '>{label}</span>"""
label_colors = {
    "Claim": "#ffa000",
    "Accuracy": "#27ae60",
    "Reason for Accuracy": "#607d8b",
    "Contribution": "#8e44ad",
    "Title": "#1976d2",
    "Authors": "#009688",
    "Year": "#9c27b0",
    "Venue": "#607d8b",
    "Relevance": "#388e3c",
    "Relevant Sentence": "#c62828",
    "Type": "#e67e22",
    "Label": "#00bfff",
    "Journal Title": "#3e2723",
    "Paragraph": "#455a64",
    "Supporting": "#1de9b6",
    "Refuting": "#d32f2f",
    "SJR Details": "#424242",
    "Original Claim": "#1976d2",
    "Articles": "#7b1fa2",
    "Summary": "#009688",
    "Overall Accuracy": "#8e44ad",
    "Verdict and Reason": "#607d8b"
}

badge_fields = [
    "Accuracy", "Contribution", "Type", "Label", "Title", "Authors", "Year", "Venue",
    "Relevance", "Relevant Sentence", "Journal Title", "Paragraph"
]