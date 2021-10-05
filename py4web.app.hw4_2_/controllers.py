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
from py4web.utils.url_signer import URLSigner

from yatl.helpers import A
from . common import db, session, T, cache, auth, signed_url
from py4web.utils.url_signer import URLSigner


url_signer = URLSigner(session)

# The auth.user below forces login.
# got help from msi
@action('index')
@action.uses(db, auth.user, session, 'index.html')
def index():
    user_email = auth.current_user.get('email')
    contacts = db(db.contacts.user_email == user_email).select()
   #phoneDict = {}
    for contact in contacts:
        phoneNumbers = db(db.phone.contact_id == contact.id).select()
        #phoneDict[str(contact.id)] = phoneNumbers
        phoneList = []
        for phone in phoneNumbers:
            phoneList.append("{0} ({1})".format(phone.phone_number, phone.kind))
        phoneString = ", ".join(phoneList)
        contact['phone_number'] = phoneString 
    return dict(c=contacts, s = url_signer)


@action('delete_contact', method=['GET', 'POST'])
@action.uses('index.html', db, session, url_signer.verify())
def delete_contact():
    parameters = request.params
    contact_id = parameters.get('contact_id', None)
    db(db.contacts.id == contact_id).delete()
    redirect(URL('index'))
  

def validateContact(form):
    firstName = form.vars['first_name']
    lastName = form.vars['last_name']
    if firstName is None:
        form.errors['first_name'] = T('Enter your first name')
    if lastName is None:
        form.errors['last_name'] = T('Enter your last name')


def validatePhone(form):
    phoneNum = form.vars['phone_number']
    phoneKind = form.vars['kind']
    if phoneNum is None:
        form.errors['phone_number'] = T('Enter your phone number')
    if phoneKind is None:
        form.errors['kind'] = T('Enter kind of phone')


@action('edit_contact/<contactID>', method=['GET', 'POST'])
@action.uses('add_contact.html', session, db)
def edit_contact(contactID=None):
    auth_user = auth.current_user
    email = auth_user.get('email')
    form = None
    contacts = db((db.contacts.user_email == email) & (db.contacts.id ==contactID)).select()
    if len(contacts) == 0:
        redirect(URL('index'))
    form = Form(db.contacts, record=contactID, deletable=False, keep_values = True, csrf_session=session, formstyle=FormStyleBulma,validation=validateContact)
    #keep_values=True
    if form.accepted:
        # We always want POST requests to be redirected as GETs.
        redirect(URL('index'))
    return dict(form=form)


@action('edit_phone_number/<phoneID>', method=['GET', 'POST'])
@action.uses('add_phone.html', session, db)
def edit_phone_number(phoneID=None):
    phoneList = db(db.phone.id == phoneID).select()
    if len(phoneList) == 0:
        redirect(URL('index'))
    contact_id = phoneList[0].contact_id
    contactList = db(db.contacts.id ==contact_id).select()
    contactRow = contactList[0]
    auth_user = auth.current_user
    userEmail = auth_user.get('email')
    contacts = db((db.contacts.user_email == userEmail) & (db.contacts.id ==contact_id)).select()
    form = Form(db.phone, record=phoneID, deletable=False, csrf_session=session, formstyle=FormStyleBulma,validation=validatePhone)
    if len(contacts) == 0:
        redirect(URL('index'))
    if form.accepted:
        redirect(URL('edit_phone', str(contact_id)))
    return dict(form=form, name = contactRow.first_name + " " + contactRow.last_name)


@action('edit_phone/<contactID>', method=['GET', 'POST'])
@action.uses('edit_phone.html', session, db)
def edit_phone(contactID=None):
    current_user_email = auth.current_user.get('email')
    contacts = db((db.contacts.id == contactID) & (db.contacts.user_email == current_user_email)).select()
    if len(contacts) == 0:
        redirect(URL('index'))
    contact = contacts[0]
    phoneNumbers = db(db.phone.contact_id == contactID).select()
    return dict(contact_id = contactID, name = contact.first_name + " " + contact.last_name, phoneNumbers=phoneNumbers, signer = url_signer) 


@action('add_phone/<contact_id>', method=['GET','POST'])
@action.uses('add_phone.html', session)
def add_phone(contact_id=None):
    current_user_email = auth.current_user.get('email')
    contact = db.contacts[contact_id]
    if contact is None or not contact.get('user_email') == current_user_email:
        redirect(URL('index'))
    form = Form(db.phone, csrf_session=session, formstyle=FormStyleBulma,validation=validatePhone)
    if form.accepted:
        phoneID = form.vars['id']
        db(db.phone.id == phoneID).update(contact_id=contact_id)
        redirect(URL('edit_phone', contact_id))
    return dict(form=form, name = contact.first_name + " " + contact.last_name)


@action('delete_phone', method=['GET','POST'])
@action.uses('edit_phone.html', db, session, url_signer.verify())
def delete_phone():
    current_user_email = auth.current_user.get('email')
    phoneID = request.params.get('phoneID')
    contactID = request.params.get('contactID')
    phoneRow = db.phone[phoneID]
    if phoneRow is None:
        redirect(URL('index'))
    contact_id = phoneRow.get('contact_id')
    contactRow = db.contacts[contact_id]
    contact_email = db.contacts.get('user_email')
    if not contact_email == current_user_email:
        redirect(URL('index'))
    db(db.phone.id == phoneID).delete()
    redirect(URL('edit_phone', str(contactID)))

@action('add_contact', method=['GET','POST'])
@action.uses('add_contact.html', session)
def add_contact():
    form = Form(db.contacts, csrf_session=session, formstyle=FormStyleBulma,validation=validateContact)
    if form.accepted:
        redirect(URL('index'))
    return dict(form=form)

