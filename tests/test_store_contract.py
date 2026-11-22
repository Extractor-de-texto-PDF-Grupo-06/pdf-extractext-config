"""Contrato del puerto ConfigStore: el doble en memoria y el adaptador de Consul se comportan igual."""


def test_crear_devuelve_la_entrada_con_su_indice(store):
    entry = store.create("web/max_file_size_mb", "10")

    assert entry.key == "web/max_file_size_mb"
    assert entry.value == "10"
    assert entry.index > 0


def test_crear_una_clave_existente_no_la_pisa(store):
    store.create("web/max_file_size_mb", "10")

    assert store.create("web/max_file_size_mb", "50") is None
    assert store.get("web/max_file_size_mb").value == "10"


def test_obtener_una_clave_inexistente_devuelve_none(store):
    assert store.get("web/no_existe") is None


def test_un_valor_vacio_se_conserva_como_texto_vacio(store):
    store.create("web/vacio", "")

    assert store.get("web/vacio").value == ""


def test_listar_devuelve_solo_las_claves_del_prefijo_ordenadas(store):
    store.create("web/timeout", "30")
    store.create("documents/limit", "100")
    store.create("web/max_file_size_mb", "10")

    keys = [entry.key for entry in store.list("web/")]

    assert keys == ["web/max_file_size_mb", "web/timeout"]


def test_listar_sin_coincidencias_devuelve_una_lista_vacia(store):
    assert store.list("web/") == []


def test_reemplazar_con_el_indice_vigente_cambia_el_valor_y_el_indice(store):
    created = store.create("web/max_file_size_mb", "10")

    updated = store.replace("web/max_file_size_mb", "50", created.index)

    assert updated.value == "50"
    assert updated.index > created.index
    assert store.get("web/max_file_size_mb").value == "50"


def test_reemplazar_con_un_indice_desactualizado_no_cambia_nada(store):
    created = store.create("web/max_file_size_mb", "10")
    store.replace("web/max_file_size_mb", "20", created.index)

    assert store.replace("web/max_file_size_mb", "50", created.index) is None
    assert store.get("web/max_file_size_mb").value == "20"


def test_borrar_quita_la_clave(store):
    store.create("web/max_file_size_mb", "10")

    store.delete("web/max_file_size_mb")

    assert store.get("web/max_file_size_mb") is None


def test_borrar_una_clave_inexistente_no_falla(store):
    store.delete("web/no_existe")


def test_hay_lider_cuando_el_almacen_funciona(store):
    assert store.has_leader() is True
