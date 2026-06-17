# In the TECHNICALS tab (tab2), replace the current code with:

with tab2:
    st.subheader("📊 Technical Indicators")
    
    # Technical indicators from model_predictor
    if len(df) > 30:
        try:
            features = create_features(df)
            
            if features.empty:
                st.warning("Unable to create technical indicators. Not enough data.")
            else:
                # Display key indicators
                col1, col2 = st.columns(2)
                
                with col1:
                    # RSI
                    from model_predictor import calculate_rsi
                    rsi = calculate_rsi(df['Close'])
                    if not rsi.empty:
                        st.subheader("RSI (Relative Strength Index)")
                        st.line_chart(rsi.tail(100))
                    else:
                        st.info("RSI data not available")
                    
                    # Volume
                    st.subheader("Volume")
                    st.bar_chart(df['Volume'].tail(60))
                
                with col2:
                    # Volatility
                    if 'Daily_Return' in features.columns:
                        st.subheader("Daily Returns")
                        st.line_chart(features['Daily_Return'].tail(100))
                    else:
                        st.info("Returns data not available")
                    
                    # MACD
                    if 'MACD' in features.columns and 'MACD_Signal' in features.columns:
                        macd_data = pd.DataFrame({
                            'MACD': features['MACD'].tail(100),
                            'Signal': features['MACD_Signal'].tail(100)
                        })
                        st.subheader("MACD")
                        st.line_chart(macd_data)
                    else:
                        st.info("MACD data not available")
        except Exception as e:
            st.error(f"Error loading technical indicators: {str(e)}")
            st.info("Showing simplified technical view")
            
            # Fallback: show basic chart
            st.subheader("Price History")
            st.line_chart(df['Close'].tail(100))
    else:
        st.info("Need at least 30 days of data for technical indicators")