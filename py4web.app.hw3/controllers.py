"""
This file defines actions, i.e. functions the URLs are mapped into
The @action(path) decorator exposed the function at URL:

    http://127.0.0.1:8000/{app_name}/{path}

If app_name == '_default' then simply

    http://127.0.0.1:8000/{path}

If path == 'index' it can be omitted:

    http://127.0.0.1:8000/

The path follows the bottlepy syntax.

@action.uses('generic.html')  indicates that the action uses the generic.html template
@action.uses(session)         indicates that the action uses the session
@action.uses(db)              indicates that the action uses the db
@action.uses(T)               indicates that the action uses the i18n & pluralization
@action.uses(auth.user)       indicates that the action requires a logged in user
@action.uses(auth)            indicates that the action requires the auth object

session, db, T, auth, and tempates are examples of Fixtures.
Warning: Fixtures MUST be declared with @action.uses({fixtures}) else your app will result in undefined behavior
"""

import uuid

from py4web import action, request, abort, redirect, URL, Field
from py4web.utils.form import Form, FormStyleBulma

from yatl.helpers import A
from . common import db, session, T, cache, auth, signed_url

from py4web.utils.url_signer import URLSigner

url_signer = URLSigner(session)

#got help from MSI

@action('index', method='GET')
@action.uses('index.html', db, session)
def view_products():
    # We get all the table rows, via a query.
    parameters = request.params
    state = parameters.get('sort','none')
    rows = db(db.product).select()
    if state == 'asc':
        rows = db(db.product).select(orderby=db.product.product_cost)
    if state == 'desc':
        rows = db(db.product).select(orderby=~db.product.product_cost)
    return dict(rows=rows, url_signer=url_signer, state=state)

@action('delete_product', method=['GET', 'POST'])
@action.uses('index.html', db, url_signer.verify(), session)
def delete_product():
    parameters = request.params
    row_id = parameters['product_id']
    db(db.product.id == row_id).delete()
    redirect(URL('index'))


@action('add_product', method=['GET', 'POST'])
@action.uses('product_form.html', session, db)
def add_product():
    form = Form(db.product, csrf_session=session, formstyle=FormStyleBulma)
    if form.accepted:
        # We always want POST requests to be redirected as GETs.
        redirect(URL('index'))
    return dict(form=form)

@action('edit_product/<product_id>', method=['GET', 'POST'])
@action.uses('product_form.html', session, db)
def edit_product(product_id=None):
    """Note that in the above declaration, the product_id argument must match
    the <product_id> argument of the @action."""
    # We read the product.
    p = db.product[product_id]
    if p is None:
        # Nothing to edit.  This should happen only if you tamper manually with the URL.
        redirect(URL('index'))
    form = Form(db.product, record=p, deletable=False, csrf_session=session, formstyle=FormStyleBulma)
    if form.accepted:
        # We always want POST requests to be redirected as GETs.
        redirect(URL('index'))
    return dict(form=form)

