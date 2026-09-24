import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
HISTORY_FILE = ROOT_DIR / "data" / "chat_history.json"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from agent import run_agent


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------

st.set_page_config(
    page_title="AI Shopping Agent",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------
# Styling
# ---------------------------------------------------------

st.markdown(
    """
    <style>

        /* ---------------------------------------------
           Main content
        --------------------------------------------- */

        .main-title {
            font-size: 2.2rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }

        .subtitle {
            color: #777;
            margin-bottom: 1.5rem;
        }

        .product-price {
            font-size: 1.5rem;
            font-weight: 700;
            margin: 0.4rem 0 1rem 0;
        }

        .availability-title {
            font-weight: 600;
            margin-top: 0.8rem;
            margin-bottom: 0.3rem;
        }


        /* ---------------------------------------------
           Sidebar
        --------------------------------------------- */

        div[data-testid="stSidebar"] {
            padding-top: 1rem;
        }


        /* ---------------------------------------------
           Chat row
        --------------------------------------------- */

        /*
         * Each chat row is a keyed Streamlit container.
         * The menu is positioned over the right side of
         * the row instead of taking visible space.
         */

        div[class*="st-key-chat-row-"] {
            position: relative;
        }


        /*
         * Keep the two columns aligned.
         */

        div[class*="st-key-chat-row-"]
        div[data-testid="stHorizontalBlock"] {
            position: relative;
            align-items: center;
            gap: 0;
        }


        /*
         * The second column is only used as an anchor
         * for the popover button.
         */

        div[class*="st-key-chat-row-"]
        div[data-testid="stHorizontalBlock"]
        > div:last-child {
            position: absolute !important;
            right: 0 !important;
            top: 50% !important;
            transform: translateY(-50%) !important;

            width: 36px !important;
            min-width: 36px !important;
            max-width: 36px !important;

            z-index: 20;
            pointer-events: none;
        }


        /*
         * Allow the actual popover button to receive clicks.
         */

        div[class*="st-key-chat-row-"]
        button[data-testid="stPopoverButton"] {
            pointer-events: auto;

            width: 32px !important;
            min-width: 32px !important;
            max-width: 32px !important;

            height: 32px !important;
            min-height: 32px !important;

            margin: 0 !important;
            padding: 0 !important;

            opacity: 0;

            display: flex !important;
            align-items: center !important;
            justify-content: center !important;

            transition: opacity 0.15s ease;
        }


        /*
         * Show the menu button only when the mouse
         * is over this chat row.
         */

        div[class*="st-key-chat-row-"]:hover
        button[data-testid="stPopoverButton"] {
            opacity: 1;
        }


        /*
         * Completely hide Streamlit's default popover
         * arrow/icon.
         */

        div[class*="st-key-chat-row-"]
        button[data-testid="stPopoverButton"] svg {
            display: none !important;
        }


        div[class*="st-key-chat-row-"]
        button[data-testid="stPopoverButton"] > * {
            display: none !important;
        }


        /*
         * Draw our own three-dot icon.
         */

        div[class*="st-key-chat-row-"]
        button[data-testid="stPopoverButton"]::after {
            content: "⋯";

            font-size: 22px;
            line-height: 1;

            display: block;
        }


        /*
         * Slightly reduce the horizontal padding of
         * chat buttons so the title has more room.
         */

        div[class*="st-key-chat-row-"]
        button[data-testid="stBaseButton-secondary"],
        div[class*="st-key-chat-row-"]
        button[data-testid="stBaseButton-primary"] {
            padding-left: 0.75rem;
            padding-right: 0.75rem;
        }


        /*
         * Keep the chat title from getting hidden
         * behind the three-dot button.
         */

        div[class*="st-key-chat-row-"]
        div[data-testid="stHorizontalBlock"]
        > div:first-child {
            padding-right: 0.15rem;
        }

    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Persistent history
# ---------------------------------------------------------

def load_chats():
    if not HISTORY_FILE.exists():
        return {}

    try:
        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError):
        return {}


def save_chats(chats):
    HISTORY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        HISTORY_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            chats,
            file,
            ensure_ascii=False,
            indent=2,
        )


# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------

if "chats" not in st.session_state:
    st.session_state.chats = load_chats()

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

if "renaming_chat_id" not in st.session_state:
    st.session_state.renaming_chat_id = None

# ---------------------------------------------------------
# Chat functions
# ---------------------------------------------------------

def create_new_chat():
    chat_id = str(uuid.uuid4())

    st.session_state.chats[chat_id] = {
        "title": "New chat",
        "created_at": datetime.now().isoformat(),
        "messages": [],
        "pinned": False,
    }

    st.session_state.current_chat_id = chat_id

    save_chats(
        st.session_state.chats
    )


def rename_chat(chat_id, new_title):
    new_title = new_title.strip()

    if not new_title:
        return

    if chat_id in st.session_state.chats:
        st.session_state.chats[chat_id]["title"] = new_title

        save_chats(
            st.session_state.chats
        )


def toggle_pin_chat(chat_id):
    if chat_id not in st.session_state.chats:
        return

    current = st.session_state.chats[chat_id].get(
        "pinned",
        False,
    )

    st.session_state.chats[chat_id]["pinned"] = not current

    save_chats(
        st.session_state.chats
    )


def delete_chat(chat_id):
    if chat_id in st.session_state.chats:
        del st.session_state.chats[chat_id]

    if st.session_state.current_chat_id == chat_id:

        if st.session_state.chats:

            sorted_chats = sorted(
                st.session_state.chats.items(),
                key=lambda item: item[1].get(
                    "created_at",
                    "",
                ),
                reverse=True,
            )

            st.session_state.current_chat_id = (
                sorted_chats[0][0]
            )

        else:
            st.session_state.current_chat_id = None

    save_chats(
        st.session_state.chats
    )


def finish_rename(chat_id):
    key = f"rename_input_{chat_id}"

    new_title = st.session_state.get(
        key,
        "",
    ).strip()

    chat = st.session_state.chats.get(chat_id)

    if chat is not None and new_title:
        chat["title"] = new_title
        save_chats(
            st.session_state.chats
        )

    st.session_state.renaming_chat_id = None
    st.rerun()


def get_current_chat():
    chat_id = st.session_state.current_chat_id

    if not chat_id:
        return None

    return st.session_state.chats.get(
        chat_id
    )


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

with st.sidebar:

    st.markdown(
        "## 🛒 AI Shopping Agent"
    )

    if st.button(
        "＋ New chat",
        use_container_width=True,
    ):
        create_new_chat()
        st.rerun()

    st.divider()

    st.markdown(
        "### Chat history"
    )

    chats = st.session_state.chats

    if not chats:

        st.caption(
            "No previous chats yet."
        )

    else:

        # Pinned chats first.
        # Within each group, newest chats first.
        sorted_chats = sorted(
            chats.items(),
            key=lambda item: (
                not item[1].get(
                    "pinned",
                    False,
                ),
                item[1].get(
                    "created_at",
                    "",
                ),
            ),
            reverse=False,
        )

        # Sort explicitly for predictable behavior:
        pinned_chats = []
        normal_chats = []

        for chat_id, chat in chats.items():

            if chat.get(
                "pinned",
                False,
            ):
                pinned_chats.append(
                    (chat_id, chat)
                )

            else:
                normal_chats.append(
                    (chat_id, chat)
                )

        pinned_chats.sort(
            key=lambda item: item[1].get(
                "created_at",
                "",
            ),
            reverse=True,
        )

        normal_chats.sort(
            key=lambda item: item[1].get(
                "created_at",
                "",
            ),
            reverse=True,
        )

        sorted_chats = (
            pinned_chats
            + normal_chats
        )

        for chat_id, chat in sorted_chats:

            title = chat.get(
                "title",
                "Untitled chat",
            )

            if chat.get("pinned", False):
                title = f"📌 {title}"

            if len(title) > 28:
                title = (
                    title[:28]
                    + "..."
                )

            is_current = (
                chat_id
                == st.session_state.current_chat_id
            )


            # ---------------------------------------------
            # Chat row
            # ---------------------------------------------

            with st.container(
                key=f"chat-row-{chat_id}"
            ):

                col1, col2 = st.columns(
                    [99, 1],
                    gap="small",
                )


                # -----------------------------------------
                # Chat button
                # -----------------------------------------

                with col1:

                    if st.session_state.renaming_chat_id == chat_id:

                        st.text_input(
                            "",
                            value=chat.get("title", "Untitled chat"),
                            key=f"rename_input_{chat_id}",
                            label_visibility="collapsed",
                            on_change=finish_rename,
                            args=(chat_id,),
                        )

                    else:

                        if st.button(
                            title,
                            key=f"chat_{chat_id}",
                            use_container_width=True,
                            type="primary" if is_current else "secondary",
                        ):
                            st.session_state.current_chat_id = chat_id
                            st.rerun()

                # -----------------------------------------
                # Three-dot menu
                # -----------------------------------------

                with col2:

                    with st.popover(
                        "",
                        use_container_width=True,
                    ):

                        # Rename
                        if st.button(
                            "✏️ Rename",
                            key=f"rename_{chat_id}",
                            use_container_width=True,
                        ):

                            st.session_state.renaming_chat_id = chat_id

                            st.rerun()


                        # Pin / Unpin
                        if chat.get(
                            "pinned",
                            False,
                        ):

                            pin_label = (
                                "📌 Unpin"
                            )

                        else:

                            pin_label = (
                                "📌 Pin"
                            )


                        if st.button(
                            pin_label,
                            key=f"pin_{chat_id}",
                            use_container_width=True,
                        ):

                            toggle_pin_chat(
                                chat_id
                            )

                            st.rerun()


                        # Delete
                        if st.button(
                            "🗑️ Delete",
                            key=f"delete_{chat_id}",
                            use_container_width=True,
                        ):

                            delete_chat(
                                chat_id
                            )

                            st.rerun()


# ---------------------------------------------------------
# Create first chat automatically
# ---------------------------------------------------------

if st.session_state.current_chat_id is None:

    create_new_chat()

    st.rerun()


current_chat = get_current_chat()


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.markdown(
    '<div class="main-title">'
    "AI Shopping Agent"
    "</div>",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "Describe what you need and the agent will search the catalog, "
    "check inventory, and show verified options."
    "</div>",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Product display
# ---------------------------------------------------------

def display_result(result):

    verified_products = result.get(
        "verified_products",
        [],
    )

    verified_count = result.get(
        "verified_count",
        0,
    )

    answer = result.get(
        "answer",
        "",
    )


    # ---------------------------------------------
    # Short explanation
    # ---------------------------------------------

    if verified_products:

        first_line = (
            answer
            .split("\n")[0]
            .strip()
        )

        if first_line:
            st.markdown(
                first_line
            )

    else:

        st.markdown(
            answer
        )


    if not verified_products:
        return


    st.divider()


    # ---------------------------------------------
    # Result count
    # ---------------------------------------------

    st.markdown(
        f"### Verified products · "
        f"{verified_count}"
    )

    if verified_count > len(
        verified_products
    ):

        st.caption(
            f"Showing "
            f"{len(verified_products)} "
            f"matching products."
        )


    # ---------------------------------------------
    # Product cards
    # ---------------------------------------------

    columns = st.columns(2)

    for index, item in enumerate(
        verified_products
    ):

        product = item["product"]
        availability = item[
            "availability"
        ]

        with columns[
            index % 2
        ]:

            with st.container(
                border=True
            ):

                st.markdown(
                    f"#### "
                    f"{product['product_name']}"
                )

                st.markdown(
                    f'<div class="product-price">'
                    f'${product["price"]:,.2f}'
                    f"</div>",
                    unsafe_allow_html=True,
                )

                col1, col2 = st.columns(2)


                # ---------------------------------
                # Left specs
                # ---------------------------------

                with col1:

                    st.caption(
                        "Processor"
                    )

                    st.write(
                        product[
                            "processor"
                        ]
                    )

                    st.caption(
                        "RAM"
                    )

                    st.write(
                        f"{product['ram_gb']} GB"
                    )

                    st.caption(
                        "SSD"
                    )

                    st.write(
                        f"{product['ssd_gb']} GB"
                    )


                # ---------------------------------
                # Right specs
                # ---------------------------------

                with col2:

                    st.caption(
                        "GPU"
                    )

                    st.write(
                        product[
                            "gpu_name"
                        ]
                    )

                    st.caption(
                        "Display"
                    )

                    st.write(
                        f"{product['display_inches']}″"
                    )

                    st.caption(
                        "OS"
                    )

                    st.write(
                        product["os"]
                    )


                st.divider()


                # ---------------------------------
                # Availability
                # ---------------------------------

                status = availability.get(
                    "status"
                )


                if status == "store_stock":

                    st.markdown(
                        "**Available in store**"
                    )

                    for store in availability.get(
                        "stores",
                        [],
                    ):

                        st.write(
                            f"📍 "
                            f"{store['location_name']} "
                            f"· "
                            f"{store['quantity']} units"
                        )


                elif status == "warehouse_delivery":

                    st.markdown(
                        "**Warehouse availability**"
                    )

                    for warehouse in availability.get(
                        "warehouses",
                        [],
                    ):

                        st.write(
                            f"📦 "
                            f"{warehouse['location_name']} "
                            f"· "
                            f"{warehouse['quantity']} units"
                        )


                    st.markdown(
                        "**Warehouse-to-store transfer**"
                    )

                    delivery = availability.get(
                        "delivery",
                        [],
                    )

                    if isinstance(
                        delivery,
                        dict,
                    ):
                        delivery = [
                            delivery
                        ]

                    for route in delivery:

                        st.write(
                            f"🚚 "
                            f"{route['destination']} "
                            f"· "
                            f"{route['min_days']}–"
                            f"{route['max_days']} days"
                        )


# ---------------------------------------------------------
# Display current chat
# ---------------------------------------------------------

for message in current_chat[
    "messages"
]:

    role = message[
        "role"
    ]

    with st.chat_message(
        role
    ):

        if role == "user":

            st.markdown(
                message["content"]
            )

        elif "result" in message:

            display_result(
                message["result"]
            )

        else:

            st.markdown(
                message["content"]
            )


# ---------------------------------------------------------
# Chat input
# ---------------------------------------------------------

if prompt := st.chat_input(
    "What laptop are you looking for?"
):

    # ---------------------------------------------
    # First message becomes chat title
    # ---------------------------------------------

    if not current_chat[
        "messages"
    ]:

        title = prompt.strip()

        if len(title) > 40:
            title = (
                title[:40]
                + "..."
            )

        current_chat[
            "title"
        ] = title


    # ---------------------------------------------
    # Preserve previous conversation
    # ---------------------------------------------

    previous_messages = (
        current_chat[
            "messages"
        ].copy()
    )


    # ---------------------------------------------
    # Save user message
    # ---------------------------------------------

    current_chat[
        "messages"
    ].append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    save_chats(
        st.session_state.chats
    )


    with st.chat_message(
        "user"
    ):

        st.markdown(
            prompt
        )


    # ---------------------------------------------
    # Run agent
    # ---------------------------------------------

    with st.chat_message(
        "assistant"
    ):

        with st.spinner(
            "Searching the catalog and checking availability..."
        ):

            try:

                result = run_agent(
                    prompt,
                    chat_history=previous_messages,
                )


                display_result(
                    result
                )


                # Save assistant result
                current_chat[
                    "messages"
                ].append(
                    {
                        "role": "assistant",
                        "content": result[
                            "answer"
                        ],
                        "result": result,
                    }
                )


                save_chats(
                    st.session_state.chats
                )


            except Exception as e:

                error_message = (
                    f"Error: {e}"
                )

                st.error(
                    error_message
                )


                current_chat[
                    "messages"
                ].append(
                    {
                        "role": "assistant",
                        "content": error_message,
                    }
                )


                save_chats(
                    st.session_state.chats
                )