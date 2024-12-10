import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
from streamlit_card import card

# # Initialize Firebase locally
# if not firebase_admin._apps:
#     cred = credentials.Certificate("firebase_credentials.json")
#     firebase_admin.initialize_app(cred)
# db = firestore.client()

# Initialize Firebase using secrets
if not firebase_admin._apps:  # Check if Firebase is already initialized
    cred_dict = st.secrets["firebase_credentials"]  # Fetch credentials from secrets
    # st.write(type(cred_dict))
    cred = credentials.Certificate(cred_dict.to_dict())  # Use the parsed credentials
    firebase_admin.initialize_app(cred)
db = firestore.client()

def get_participants():
    participants_ref = db.collection("participants")
    docs = participants_ref.stream()
    participants = []
    for doc in docs:
        participant = doc.to_dict()
        participant['name'] = doc.id  # Store document ID as name
        participants.append(participant)
    return participants

def get_gift_mapping():
    mapping_ref = db.collection("mappings").document("assignments")
    doc = mapping_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        return {}

def update_wishlist(participant_name, wishlist_items):
    participant_ref = db.collection("participants").document(participant_name)
    participant_ref.set({
        "wishlist": [item.strip() for item in wishlist_items.split(",")],
        "has_wishlist": True
    }, merge=True)
    return "Wishlist updated successfully!"

st.markdown("""
<style>
    .center-content {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    .bottom-content {
        display: flex;
        justify-content: flex-end;
        height: 100%;
        flex-direction: column;
    }
</style>
""", unsafe_allow_html=True)


# Sidebar Navigation
st.sidebar.title("Świąteczna wymiana prezentów 🎄")
st.text("")
menu = st.sidebar.selectbox(
    "Wybierz podstronę:",
    ["🎁 Komu robię prezent?", "📝 Moja lista życzeń", "🎅 Tegoroczni uczestnicy"]
)

# Main Page Logic
if "Tegoroczni" in menu:
    # Fetch participants (replace with Firestore fetching logic if applicable)
    participants = get_participants()  # Ensure this fetches the latest data
    
    st.title("🎅 Lista uczestników 🤶")

    st.write("Ta strona przedstawia w jednym miejscu wszystkich uczestników wraz z informacją czy przygotowali już swoją listę życzeń. Nie jest interaktywna, tak więc klikanie na poszczególne komórki nie przeniesie nas w żadne inne miejsce - do tego celu wykorzystać trzeba rozwijane menu z lewej strony.")

    data = [
        {"Uczestnik": p["name"], 
        "Lista życzeń": "✅ Gotowa! " if p.get("has_wishlist") else "⏳ W trakcie przygotowywania"} 
        for p in participants
    ]
    df = pd.DataFrame(data)

    # Reset the index to avoid displaying it in st.table()
    df = df.reset_index(drop=True)

    # Render the styled table in Streamlit
    st.dataframe(df, use_container_width=True, hide_index=True)


elif "Moja" in menu:
    st.title("📝 Moja lista życzeń")

    st.write("Ta strona sluży za narzędzie do stworzenia swojego listu do Mikołaja. Po wybraniu swojego imienia pokaże się lista ktorą można swobodnie edytować - dodawać nowe pozycje lub usuwać istniejące.")
    participants = get_participants()
    participant_names = [p['name'] for p in participants]
    participant_name = st.selectbox("Wybierz swoje imię", participant_names, index=None)

    if participant_name:
        participant_ref = db.collection("participants").document(participant_name)
        participant_doc = participant_ref.get()
        if participant_doc.exists:
            current_wishlist = participant_doc.to_dict().get("wishlist", [])
        else:
            current_wishlist = []

        # Display the wishlist with edit and remove functionality
        st.write("### Twoja aktualna lista życzeń:")
        for idx, item in enumerate(current_wishlist):
            col1, col2 = st.columns([3, 2], vertical_alignment="bottom")
            with col1:
                new_value = st.text_input(f"Pozycja {idx+1}", value=item, key=f"edit_{idx}", disabled=False)

            with col2:
                # st.markdown('<div class="bottom-content">', unsafe_allow_html=True)
                if st.button("Usuń", key=f"delete_{idx}", use_container_width=False):
                    current_wishlist.pop(idx)
                    participant_ref.update({"wishlist": current_wishlist, "has_wishlist": len(current_wishlist) > 0})
                    st.toast("❌ Pozycja usunięta!")
                    st.rerun()
                # st.markdown('</div>', unsafe_allow_html=True)

        # Input field to add new items
        new_item = st.text_input("Dodaj nową pozycję")
        if st.button("Dodaj pozycję"):
            if new_item:
                current_wishlist.append(new_item)
                participant_ref.update({"wishlist": current_wishlist, "has_wishlist": len(current_wishlist) > 0})
                st.toast("✅ Pozycja dodana!")
                st.rerun() 

elif "Komu" in menu:
    st.title("🎁 Sprawdź przypisaną listę")
    participants = get_participants()
    participant_names = [p['name'] for p in participants]
    participant_name = st.selectbox("Wybierz swoje imię", participant_names, index=None)

    if participant_name:
        gift_mapping = get_gift_mapping()
        assigned_person = gift_mapping.get(participant_name)
        if assigned_person:
            assigned_ref = db.collection("participants").document(assigned_person)
            assigned_doc = assigned_ref.get()
            st.write(f"### Twoja wylosowana osoba to: {assigned_person}")
            if assigned_doc.exists:
                assigned_data = assigned_doc.to_dict()
                assigned_wishlist = assigned_data.get("wishlist", [])
                if assigned_wishlist:
                    st.write(f"### A jej lista życzeń:")
                    for item in assigned_wishlist:
                        st.write(f"- {item}")
                else:
                    st.warning(f"Niestety ta osoba nie stworzyła jeszcze listy życzeń.")
            else:
                st.error(f"{assigned_person} - niestety ta osoba nie istnieje w bazie.")
        else:
            st.error("Nie znalezlismy twojej pary, zgłoś problem na rodzince!")


st.sidebar.markdown("## Wesołych Świąt! 🦌🛷☃️")
