import streamlit as st
import requests
import math
import time

# Initialize page number in session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 0

st.title("Biological Data Explorer")

# Sidebar inputs
st.sidebar.title("Search Parameters")
gene = st.sidebar.text_input("Enter a gene name", "BRCA1")
results_per_page = st.sidebar.slider("Results per page", 5, 20, 5)

if st.sidebar.button("Search"):
    st.session_state.current_page = 0  # Reset to page 0 on new search

# API Call logic
with st.spinner('Fetching data from NCBI...'):
    search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gene&term={gene}&retmode=json"
    response = requests.get(search_url)

    # Check if the request was successful
    if response.status_code == 200:
        total_count_response = response.json()
    
        # Check if the key exists before accessing it
        if 'esearchresult' in total_count_response:
            total_count = int(total_count_response['esearchresult']['count'])
            total_pages = math.ceil(total_count / results_per_page)
        

            # Calculate start index
            retstart = st.session_state.current_page * results_per_page

            # Fetch specific page data
            paginated_url = f"{search_url}&retmax={results_per_page}&retstart={retstart}"
            response = requests.get(paginated_url).json()
            id_list = response['esearchresult']['idlist']

            if id_list:
                ids_to_fetch = ",".join(id_list)
                summary_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=gene&id={ids_to_fetch}&retmode=json"
        
                # Add a delay for the second call too, to be safe
                time.sleep(0.5) 
                summary_response = requests.get(summary_url).json()

                # DEFENSIVE CHECK: Ensure 'result' exists
                if 'result' in summary_response:
                    for uid in id_list:
                        # Use .get() to avoid KeyError if the UID is missing
                        result = summary_response['result'].get(uid, {})
                        st.write(f"**Gene:** {result.get('name', 'N/A')}")
                        st.write(f"**Description:** {result.get('description', 'N/A')}")
                        st.divider()
                else:
                    # If 'result' is missing, NCBI often provides an 'error' or 'uids' field
                    st.error("Could not fetch details for these genes. The API returned an unexpected format.")
                    if 'error' in summary_response:
                        st.write(f"API Error: {summary_response['error']}")

            # --- Calculate Ranges ---
            start_num = (st.session_state.current_page * results_per_page) + 1
            # 'min' ensures the end number doesn't go higher than the actual total count
            end_num = min((st.session_state.current_page + 1) * results_per_page, total_count)

            # --- Display Header ---
            st.metric(label="Total Results Found", value=total_count)
            st.write(f"Showing results **{start_num}** to **{end_num}** of **{total_count}**")

            # --- Navigation Buttons ---
            col1, col2, col3 = st.columns([1, 2, 1])

            with col1:
                # Disable "Previous" button if we are on the first page
                if st.button("Previous") and st.session_state.current_page > 0:
                    st.session_state.current_page -= 1
                    st.rerun()

            with col3:
                # Disable "Next" button if we are on the last page
                if st.button("Next") and st.session_state.current_page < total_pages - 1:
                    st.session_state.current_page += 1
                    st.rerun()
        else:
            st.error("The API returned data, but it didn't contain the expected results.")
            st.write("Raw response:", total_count_response) 
    else:
        st.error(f"API request failed with status code: {response.status_code}")


