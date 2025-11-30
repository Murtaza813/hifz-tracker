def run_juzhali_assistant(student_data_df, student_id):
    """Juzhali assistant for rolling page revision"""
    
    if student_data_df is None or student_data_df.empty:
        st.error("❌ No student data available.")
        return
    
    df = student_data_df.copy()
    
    # Header
    st.markdown("""
    <div style="text-align: center; padding: 30px 0;">
        <h1 style="background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%); 
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                   font-size: 3em; margin: 0;">
            🔄 Juzhali Assistant
        </h1>
        <p style="color: #6b7280; font-size: 1.2em; margin-top: 10px;">
            Rolling 10-page revision before new Jadeed • Track retention & performance
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-detect Juzhali range
    last_jadeed_page = get_last_jadeed_page(df)
    
    if last_jadeed_page is None:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); 
                    padding: 30px; border-radius: 15px; text-align: center; margin: 20px 0;">
            <h2 style="color: #dc2626; margin: 0 0 15px 0;">⚠️ No Jadeed Sessions Found!</h2>
            <p style="color: #991b1b; font-size: 1.1em; margin: 10px 0;">
                Juzhali tracks the 10 pages BEFORE your current Jadeed page.
            </p>
            <div style="background: white; padding: 20px; border-radius: 10px; margin-top: 20px;">
                <h3 style="color: #3b82f6;">💡 Getting Started:</h3>
                <p style="color: #374151;">
                    Record your first <strong>Jadeed session</strong> to activate Juzhali tracking!
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    if 'juzhali_length' not in st.session_state:
        st.session_state.juzhali_length = 10
    
    # Calculate range
    juzhali_end = last_jadeed_page
    juzhali_start = max(1, juzhali_end - st.session_state.juzhali_length + 1)
    
    # FIX 1: Define page_range_list here
    page_range_list = list(range(juzhali_start, juzhali_end + 1))
    
    # Display current range
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); 
                    padding: 20px; border-radius: 15px; border-left: 5px solid #3b82f6;">
            <h2 style="color: #1e40af; margin: 0 0 10px 0;">
                📖 Current Juzhali Range: Pages {juzhali_start} - {juzhali_end}
            </h2>
            <p style="color: #1e3a8a; margin: 5px 0;">
                🔗 Auto-connected: Last Jadeed = Page {juzhali_end} | {st.session_state.juzhali_length}-page window
            </p>
            <p style="color: #059669; margin: 5px 0; font-weight: bold;">
                ✅ Next Jadeed will start from Page {juzhali_end + 1}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.show_juzhali_config = True
    
    # Configuration
    if st.session_state.get('show_juzhali_config', False):
        with st.expander("⚙️ Juzhali Configuration", expanded=True):
            st.markdown(f"""
            <div style="background: #f3f4f6; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                <p style="margin: 0; color: #374151;">
                    <strong>Current Jadeed:</strong> Page {juzhali_end}<br>
                    <strong>How it works:</strong> Juzhali = X pages BEFORE your current Jadeed page
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            new_length = st.selectbox(
                "Juzhali Window Size (pages to review)",
                options=[10, 15, 20, 25, 30],
                index=[10, 15, 20, 25, 30].index(st.session_state.juzhali_length),
                help="How many pages to review before Jadeed"
            )
            
            preview_start = max(1, juzhali_end - new_length + 1)
            st.info(f"📊 Preview: Pages {preview_start} to {juzhali_end}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save Changes", type="primary", use_container_width=True):
                    st.session_state.juzhali_length = new_length
                    st.session_state.show_juzhali_config = False
                    st.success("Settings updated!")
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", use_container_width=True):
                    st.session_state.show_juzhali_config = False
                    st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Filter Juzhali data
    temp_data = df.copy()
    temp_data['Page_Str'] = temp_data['Page'].astype(str)
    temp_data['Is_Single_Page'] = temp_data['Page_Str'].str.match(r'^\d+$')
    temp_data['Page_Numeric'] = pd.to_numeric(temp_data['Page_Str'], errors='coerce')
    
    juzhali_data = temp_data[
        (temp_data['Session_Type'] == 'Juzhali') &
        (temp_data['Is_Single_Page'] == True) &
        (temp_data['Page_Numeric'].notna()) &
        (temp_data['Page_Numeric'] >= juzhali_start) &
        (temp_data['Page_Numeric'] <= juzhali_end)
    ].copy()
    
    # Health Score
    st.markdown('<div class="section-header">📊 Juzhali Retention Health</div>', unsafe_allow_html=True)
    
    if juzhali_data.empty:
        st.markdown(f"""
        <div class="info-section">
            <h3 style="margin: 0 0 10px 0;">ℹ️ No Sessions Recorded Yet</h3>
            <p style="margin: 0;">
                Start recording Juzhali sessions for pages {juzhali_start}-{juzhali_end} below!
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Look for overall session grades (Session_Summary entries)
        juzhali_grades_data = juzhali_data[
            (juzhali_data['Core_Mistake'] == 'Session_Summary') & 
            (juzhali_data['Overall_Grade'].notna())
        ]
        
        if not juzhali_grades_data.empty:
            # Convert Arabic grades to numeric
            juzhali_grades = juzhali_grades_data['Overall_Grade'].apply(grade_to_numeric).dropna()
            
            if not juzhali_grades.empty:
                avg_grade = juzhali_grades.mean()
                score = (avg_grade / 10) * 100  # Convert to percentage
                
                health_class = get_health_color_class(score)
                health_msg = get_health_message(score)
                
                st.markdown(f"""
                <div class="health-card {health_class}">
                    <h2 style="margin: 0 0 15px 0;">Juzhali Retention Health</h2>
                    <h1 style="margin: 0; font-size: 3.5em;">{score:.1f}%</h1>
                    <p style="margin: 15px 0 0 0; font-size: 1.3em; font-weight: bold;">{health_msg}</p>
                    <div style="background: rgba(255,255,255,0.3); border-radius: 10px; height: 15px; 
                                margin-top: 20px; overflow: hidden;">
                        <div style="background: white; height: 100%; width: {score}%; 
                                    transition: width 0.5s ease;"></div>
                    </div>
                    <p style="margin: 15px 0 0 0; font-size: 0.95em; opacity: 0.9;">
                        Based on {len(juzhali_grades)} session grades • Average: {avg_grade:.1f}/10
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="info-section">
                    <h3 style="margin: 0 0 10px 0;">📊 No Overall Grades Yet</h3>
                    <p style="margin: 0;">
                        Start recording sessions with overall grades to see health scores!
                    </p>
                </div>
                """, unsafe_allow_html=True)
        else:
            # Fallback to old calculation if no overall grades
            tot = juzhali_data['Mistake_Count'].sum()
            tal = juzhali_data[juzhali_data['Mistake_Type'] == 'Talqeen']['Mistake_Count'].sum()
            score = 100 * (1 - (tal / tot)) if tot > 0 else 100
            
            health_class = get_health_color_class(score)
            health_msg = get_health_message(score)
            
            st.markdown(f"""
            <div class="health-card {health_class}">
                <h2 style="margin: 0 0 15px 0;">Juzhali Retention Health</h2>
                <h1 style="margin: 0; font-size: 3.5em;">{score:.1f}%</h1>
                <p style="margin: 15px 0 0 0; font-size: 1.3em; font-weight: bold;">{health_msg}</p>
                <div style="background: rgba(255,255,255,0.3); border-radius: 10px; height: 15px; 
                            margin-top: 20px; overflow: hidden;">
                    <div style="background: white; height: 100%; width: {score}%; 
                                transition: width 0.5s ease;"></div>
                </div>
                <p style="margin: 15px 0 0 0; font-size: 0.95em; opacity: 0.9;">
                    Total: {int(tot)} mistakes • Talqeen: {int(tal)} • Based on {len(juzhali_data)} sessions
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Page performance map
    st.markdown('<div class="section-header">🗺️ Page Performance Map</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <p style="text-align: center; color: #6b7280; font-size: 1.1em;">
        Performance overview of Pages {juzhali_start} - {juzhali_end}
    </p>
    """, unsafe_allow_html=True)
    
    page_health_map = {}
    
    for page_num in page_range_list:
        p_data = juzhali_data[juzhali_data['Page_Numeric'] == page_num]
        
        if p_data.empty:
            status = "not_tested"
            color_code = "#e5e7eb"
            font_color = "#9ca3af"
            mistake_summary = "Not tested"
        else:
            talqeen_sum = p_data[p_data['Mistake_Type'] == 'Talqeen']['Mistake_Count'].sum()
            tambeeh_sum = p_data[p_data['Mistake_Type'] == 'Tambeeh']['Mistake_Count'].sum()
            
            if talqeen_sum > 0:
                status = "critical"
                color_code = "#fee2e2"
                font_color = "#dc2626"
                mistake_summary = f"{int(talqeen_sum)} Tal / {int(tambeeh_sum)} Tam"
            elif tambeeh_sum >= 3:
                status = "weak"
                color_code = "#fef3c7"
                font_color = "#d97706"
                mistake_summary = f"{int(tambeeh_sum)} Tam"
            else:
                status = "good"
                color_code = "#d1fae5"
                font_color = "#059669"
                mistake_summary = "Good ✓"
        
        page_health_map[page_num] = {
            "status": status,
            "color": color_code,
            "text": font_color,
            "summary": mistake_summary
        }
    
    # Display map
    num_cols = 5
    num_rows = (len(page_range_list) + num_cols - 1) // num_cols
    
    for row_idx in range(num_rows):
        cols = st.columns(num_cols)
        for col_idx in range(num_cols):
            page_idx = row_idx * num_cols + col_idx
            if page_idx >= len(page_range_list):
                break
            
            page_num = page_range_list[page_idx]
            data = page_health_map[page_num]
            
            with cols[col_idx]:
                st.markdown(f"""
                <div class="page-box" style="background-color: {data['color']}; 
                                            border: 2px solid {data['text']};">
                    <div style="color: {data['text']}; font-size: 1.2em; font-weight: bold;">
                        Page {page_num}
                    </div>
                    <div style="color: {data['text']}; font-size: 0.85em; margin-top: 5px;">
                        {data['summary']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Session entry
    st.markdown('<div class="section-header">📝 Record New Session</div>', unsafe_allow_html=True)
    
    with st.form(key='juzhali_session_form'):
        col1, col2 = st.columns(2)
        with col1:
            session_date = st.date_input("📅 Session Date", datetime.now().date())
        with col2:
            st.markdown(f"**Session Type:** Juzhali (Pages {juzhali_start}-{juzhali_end})")
        
        st.markdown("---")
        
        selected_pages = st.multiselect(
            "📄 Select Pages Tested (in order)",
            options=[str(i) for i in page_range_list],
            help="Choose pages you tested in this session"
        )
        
        # FIX 2: Add submit button to the form
        start_entry = st.form_submit_button("✅ Start Recording Mistakes", type="primary", use_container_width=True)
    
    # Initialize session state
    if 'juz_page_entries' not in st.session_state:
        st.session_state.juz_page_entries = {}
    
    if 'juz_session_started' not in st.session_state:
        st.session_state.juz_session_started = False
    
    if start_entry and selected_pages:
        st.session_state.juz_session_started = True
        st.session_state.juz_session_date = session_date
        st.session_state.juz_selected_pages = selected_pages
        st.session_state.juz_page_entries = {}
    
    # Page-by-page entry
    if st.session_state.juz_session_started and hasattr(st.session_state, 'juz_selected_pages'):
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">📄 Page-by-Page Entry</div>', unsafe_allow_html=True)
        
        for idx, page_num in enumerate(st.session_state.juz_selected_pages):
            with st.expander(f"📄 Page {page_num} - Question #{idx + 1}", expanded=(idx == 0)):
                
                col1, col2 = st.columns(2)
                with col1:
                    talqeen = st.number_input(
                        "🔴 Talqeen Mistakes",
                        min_value=0, step=1,
                        key=f'juz_talqeen_{page_num}_{idx}'
                    )
                with col2:
                    tambeeh = st.number_input(
                        "🟡 Tambeeh Mistakes",
                        min_value=0, step=1,
                        key=f'juz_tambeeh_{page_num}_{idx}'
                    )
                
                st.markdown("**📏 Tajweed Classification (Optional)**")
                col1, col2 = st.columns(2)
                with col1:
                    tajweed_mistake = st.selectbox(
                        "Ahkaam Error",
                        STANDARD_AHKAAM,
                        key=f'juz_ahkaam_{page_num}_{idx}'
                    )
                with col2:
                    tajweed_note = st.text_input(
                        "Additional Note",
                        placeholder="Optional",
                        key=f'juz_taj_note_{page_num}_{idx}'
                    )
                
                st.markdown("**🗣️ Makharij Classification (Optional)**")
                col1, col2 = st.columns(2)
                with col1:
                    makharij_mistake = st.selectbox(
                        "Makharij Error",
                        STANDARD_MAKHARIJ,
                        key=f'juz_makh_{page_num}_{idx}'
                    )
                with col2:
                    makharij_note = st.text_input(
                        "Additional Note",
                        placeholder="Optional",
                        key=f'juz_makh_note_{page_num}_{idx}'
                    )
                
                specific_details = []
                core_mistake = 'Hifz'
                
                if tajweed_mistake != 'N/A':
                    core_mistake = 'Tajweed'
                    detail = tajweed_mistake
                    if tajweed_note:
                        detail += f" ({tajweed_note})"
                    specific_details.append(detail)
                
                if makharij_mistake != 'N/A':
                    core_mistake = 'Makharij'
                    detail = makharij_mistake
                    if makharij_note:
                        detail += f" - {makharij_note}"
                    specific_details.append(detail)
                
                if tajweed_mistake != 'N/A' and makharij_mistake != 'N/A':
                    core_mistake = 'Mixed'
                
                specific_mistake_detail = "; ".join(specific_details) if specific_details else f"Page {page_num}"
                
                st.session_state.juz_page_entries[page_num] = {
                    'talqeen': talqeen,
                    'tambeeh': tambeeh,
                    'core_mistake': core_mistake,
                    'specific_mistake': specific_mistake_detail
                }
        
        # =========================================================================
        # NEW: OVERALL SESSION GRADE SECTION
        # =========================================================================
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">🎯 Overall Session Grade</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); 
                    padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h4 style="color: #1e40af; margin: 0 0 10px 0;">📊 Session Performance Summary</h4>
            <p style="color: #374151; margin: 0;">
                Based on today's performance across all pages, provide an overall grade for this Juzhali session.
                This grade will be used to calculate your Juzhali Health Score.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            overall_grade = st.selectbox(
                "Overall Session Grade",
                options=["جيد جدا", "جيد", "متوسط", "ضعيف"],
                format_func=lambda x: {
                    "جيد جدا": "جيد جدا 🌟 (Excellent)",
                    "جيد": "جيد ✅ (Good)", 
                    "متوسط": "متوسط 🟡 (Average)",
                    "ضعيف": "ضعيف ❌ (Weak)"
                }[x],
                help="Overall evaluation of today's Juzhali session"
            )
        
        with col2:
            # Show what this grade means for health score
            grade_to_score = {
                "جيد جدا": "100%",
                "جيد": "80%", 
                "متوسط": "60%",
                "ضعيف": "40%"
            }
            st.markdown(f"""
            <div style="background: rgba(16, 185, 129, 0.1); 
                        padding: 15px; border-radius: 8px; text-align: center;
                        border: 2px solid #10b981;">
                <p style="margin: 0; color: #047857; font-size: 0.9em;">Health Impact</p>
                <h3 style="margin: 5px 0 0 0; color: #059669;">{grade_to_score[overall_grade]}</h3>
            </div>
            """, unsafe_allow_html=True)
        
        # Session notes
        session_notes = st.text_area(
            "Session Notes (Optional)",
            placeholder="Any observations about today's session...",
            height=80
        )
        
        # Store overall grade in session state
        st.session_state.juz_overall_grade = overall_grade
        st.session_state.juz_session_notes = session_notes
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # =========================================================================
        # SUBMIT BUTTON - UPDATED TO SAVE OVERALL GRADE
        # =========================================================================
        if st.button("💾 Submit Complete Session", type="primary", use_container_width=True):
            # Save logic here - including overall grade
            try:
                from database import append_new_session
                
                # Save individual page entries
                for page_num, page_data in st.session_state.juz_page_entries.items():
                    session_data = {
                        'date': st.session_state.juz_session_date,
                        'sipara': None,
                        'page_tested': page_num,
                        'talqeen_count': page_data['talqeen'],
                        'tambeeh_count': page_data['tambeeh'],
                        'core_mistake_type': page_data['core_mistake'],
                        'specific_mistake': page_data['specific_mistake'],
                        'overall_grade': None,  # Individual pages don't get grades
                        'notes': f"Page {page_num} - {st.session_state.juz_session_notes}" if st.session_state.juz_session_notes else f"Page {page_num}"
                    }
                    
                    # Save each page entry
                    append_new_session(student_id, 'Juzhali', session_data)
                
                # Save OVERALL SESSION with grade
                overall_session_data = {
                    'date': st.session_state.juz_session_date,
                    'sipara': None,
                    'page_tested': f"Pages {', '.join(st.session_state.juz_selected_pages)}",
                    'talqeen_count': 0,
                    'tambeeh_count': 0,
                    'core_mistake_type': 'Session_Summary',
                    'specific_mistake': 'Overall Session Evaluation',
                    'overall_grade': st.session_state.juz_overall_grade,  # ✅ This is the key line!
                    'notes': st.session_state.juz_session_notes or "Juzhali session completed"
                }
                
                append_new_session(student_id, 'Juzhali', overall_session_data)
                
                # Reset session state
                st.session_state.juz_session_started = False
                st.session_state.juz_page_entries = {}
                st.session_state.juz_overall_grade = None
                st.session_state.juz_session_notes = None
                
                st.success(f"✅ Successfully recorded session for {len(st.session_state.juz_selected_pages)} pages with overall grade: {overall_grade}!")
                st.markdown(f"""
                <div class="success-section">
                    <p style="margin: 0; text-align: center;">
                        🔗 Next Jadeed will automatically start from Page <strong>{juzhali_end + 1}</strong>
                    </p>
                </div>
                """, unsafe_allow_html=True)
                st.balloons()
                
                # Auto-refresh after 3 seconds
                import time
                with st.spinner("Refreshing in 3 seconds..."):
                    time.sleep(3)
                
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error saving session: {str(e)}")
