import streamlit as st
import pickle
import tempfile
import os
from streamlit_searchbox import st_searchbox
from spellchecker import SpellChecker
import pandas as pd
from st_aggrid import AgGrid, GridUpdateMode,  JsCode
from st_aggrid.grid_options_builder import GridOptionsBuilder
from streamlit.runtime.legacy_caching import caching
from cards import WildberriesParser, AptekaParser
from gradio_client import Client
from indexer import indexer


def search_category(stu_name, wb):
    global indexer, clf # тут используем Saiga2 13B - российская open source LLM модель высокого уровня. На время участия разместили на бесплатных мощностях. При желании, развёртывается в формате микросервиса. Исходный код: 
    nlp = indexer[clf.predict([stu_name])[0]]
    req = f"""Ты сотрудник склада маркетплейса.
        К какой категории ты отнесёшь товар "{stu_name}". Напиши исключительно только название категории в именительном падеже, не выдумывай.
        Твои коллеги предлагают такие варианты, но они могут ошибаться:
        1. {nlp}
        2. {wb}"""
    client = Client("https://ilyagusev-saiga2-13b-gguf.hf.space/--replicas/4400m/")
    result = client.predict(
        [[req ,None]],  
        "Hello!!", 
        0, 
        10, 
        0, 
        api_name="/bot"
    )
    return result[-1][-1]
    

@st.cache_resource
def load_all():
    global clf
    data = pd.read_csv('stuExampleList.csv', delimiter=';', encoding='windows-1251')
    df_parametrs = pd.read_csv('parametrs.csv', delimiter=';', encoding='windows-1251')
    with open('classifer.pkl', 'rb') as classiferModelFile:
        clf = pickle.load(classiferModelFile)
    return data, clf

def word_is_russian(word):
    kirill = ('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
    find_kirill = [x for x in kirill if x in word.lower()]
    if len(find_kirill) >= len(word)//2:
        return True
    return False


def check_word(word):
    spell = SpellChecker(language=('ru' if word_is_russian(word) else 'en'))
    if spell.correction(word):
        return spell.correction(word)
    else:
        return word


def main():
    st.header("""Генерация наименования и характеристик СТЕ""")
    
    def show_parametrs(params:dict, flag):
        def data_upload():
            df = pd.DataFrame.from_dict(params)
            # st.session_state.generate_log = pd.DataFrame.from_dict(params)
            for del_row in ['is_variable', 'charc_type', 'variable_values', 'is_unifying']:
                try:
                    df.drop(del_row, axis=1, inplace=True)
                except:
                    pass
            return df

        st.header("Таблица характеристик")

        if 'grid' in st.session_state and not flag:
            grid_table = st.session_state['grid']
            df = pd.DataFrame(grid_table['data'])
        else:
            df = data_upload()

        gd = GridOptionsBuilder.from_dataframe(df)
        gd.configure_column('name', header_name="Характеристика", editable=True)
        gd.configure_column('value', header_name="Значение", editable=True)
        gridOptions = gd.build()

        def update():
            caching.clear_cache()

        button = st.button("Добавить харакктеристику")       

        if "button_state" not in st.session_state:
            st.session_state.button_state = False

        if button or st.session_state.button_state:
            st.session_state.button_state = True 
            df.loc[len(df.index)] = ["", ""]

        grid_table = AgGrid(df,
                            gridOptions=gridOptions,
                            fit_columns_on_grid_load=True,
                            height=500,
                            width='100%',
                            theme="streamlit",
                            key= 'unique',
                            update_mode=GridUpdateMode.GRID_CHANGED,
                            reload_data=True,
                            allow_unsafe_jscode=True,
                            editable=True
                            )
        st.session_state['grid'] = grid_table
        # if 'grid' not in st.session_state:
            # st.session_state['grid'] = grid_table

    def search_wikipedia(searchterm: str):
        text_variants = []
        if searchterm:
            text_variants.append(searchterm)
            words_list = searchterm.split()
            if len(words_list) > 1:
                text_variants.append(" ".join(check_word(word) for word in words_list))
                text_variants.append(" ".join(words_list[:-1]) + " " + check_word(words_list[-1]))
            if len(words_list) == 1:
                text_variants.append(check_word(words_list[-1]))
        return text_variants

    stu_fullname = st_searchbox(
        search_wikipedia,
    key="wiki_searchbox",
        label='Полное название СТЕ',
        edit_after_submit='option'
    )
    search_button = st.button("Начать")

    if (search_button or st.session_state.stu_name_loaded) and st.session_state.stu_fullname != stu_fullname:
        st.session_state.stu_name_loaded = True
        categories_data = list(set(pr_data['Наименование конечной категории Портала']))
        stu_image = st.file_uploader("Загрузите изображение СТЕ", accept_multiple_files=False)
        if stu_image:
            st.image(stu_image, caption='Изображение СТЕ')
        data_product_wb = WildberriesParser.get_product_info(stu_fullname)
        if not st.session_state.stu_category_loaded or st.session_state.stu_fullname != stu_fullname:
            st.session_state.stu_category_loaded = True
            clf_stu_category_result = search_category(stu_fullname, data_product_wb['category'])
            st.session_state.stu_category = clf_stu_category_result
        else:
            clf_stu_category_result = st.session_state.stu_category
        
        if clf_stu_category_result not in categories_data:
            categories_data.append(clf_stu_category_result)

        if data_product_wb['brand'].lower() not in stu_fullname.lower():
            st.write('Вы не ввели производителя, был выбран продукт средних характеристик')

        stu_manufacturer = st.text_input("Производитель", value=data_product_wb['brand'])

        stu_category = st.selectbox(
            label='Категориия СТЕ',
            options=categories_data,
            index=categories_data.index(clf_stu_category_result)
        )
        
        if data_product_wb:
            st.session_state.generate_log = data_product_wb['features']
            show_parametrs( 
                data_product_wb['features'],
                st.session_state.stu_fullname != stu_fullname
            )

        flag_table_changed = False
        try:
            _ = st.session_state['grid']
            flag_table_changed = True
        except:
            pass
        output_df = pd.DataFrame.from_dict(st.session_state.generate_log)
        output_df['profit'] = pd.Series([1 for x in range(len(output_df.index))]) 
        if flag_table_changed:
            updated_df = pd.DataFrame(st.session_state['grid']['data'])
            col2, col3 = st.columns(2)
            with col2:
                st.write(output_df['value'])
            with col3:
                st.write(updated_df['value'])
            output_df['profit'] = pd.Series([1 if output_df['value'][x] == updated_df['value'][x] else 0 for x in range(len(output_df.index))]) 
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'tmp.xlsx')
            output_df.to_excel(path, engine="openpyxl")
            with open(path, 'rb') as file:
                download2 = st.download_button(
                    label="Download data as Excel",
                    data=file,
                    file_name='large_df.xlsx',
                    mime='application/vnd.ms-excel'
                )

        st.markdown("![Alt Text](https://media.giphy.com/media/vFKqnCdLPNOKc/giphy.gif)")

try:
    _ = st.session_state.stu_name_loaded
except:
    st.session_state.stu_name_loaded = False

try:
    _ = st.session_state.stu_category_loaded
except:
    st.session_state.stu_category_loaded = False

try:
    _ = st.session_state.stu_fullname
except:
    st.session_state.stu_fullname = "None"

pr_data, clf = load_all()
if __name__ == "__main__":
    main()
