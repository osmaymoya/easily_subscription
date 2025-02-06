from odoo import http
from odoo.service import db
from odoo.sql_db import db_connect
import requests
import re

class CustomSignupController(http.Controller):

    @http.route('/signup', type='http', auth='public', website=True)
    def signup_form(self, **post):
        # Mostrar el formulario si no se han enviado datos
        if not post:
            return http.request.render('easily_subscription.signup_form_template', {})

        # Procesar los datos del formulario
        values = {}
        email = post.get('email')
        values['email'] = email
        fullname = post.get('fullname')
        values['fullname'] = fullname
        password = post.get('password')
        values['password'] = password
        lang = post.get('lang')
        values['lang'] = lang
        company_name = post.get('company_name')
        values['company_name'] = company_name
        recaptcha_response = post.get('g-recaptcha-response')  # Token de reCAPTCHA

        # Validar los datos
        errors = {}
        if not all([email, fullname, password, lang, company_name]):
            errors['error'] = 'Todos los campos son obligatorios.'
        elif not self._validate_email(email):
            errors['email_error'] = 'El correo electrónico no tiene un formato válido.'
        elif not self._validate_fullname(fullname):
            errors['fullname_error'] = 'El nombre de usuario no puede tener más de 50 caracteres.'
        elif not self._validate_password(password):
            errors['password_error'] = 'La contraseña debe tener al menos 8 caracteres, una mayúscula, una minúscula y un número.'
        elif not self._validate_recaptcha(recaptcha_response):
            errors['captcha_error'] = 'Por favor, completa el CAPTCHA.'

        if errors:
            return http.request.render('easily_subscription.signup_form_template', {**values, **errors})

        try:

            # Crear la base de datos
            db_name = email.replace('@', '').replace('.', '')
            db_password = "odoo"

            db.exp_create_database(db_name, False, lang, db_password)

            # Conectar a la nueva base de datos
            with db_connect(db_name).cursor() as cr:
                env = http.request.env(cr=cr)

                # Instalar el módulo odoo-royal
                module = env['ir.module.module'].sudo().search([('name', '=', 'odoo-royal')], limit=1)
                if module:
                    module.button_immediate_install()  # Instalar el módulo

                # Obtener el país de Estados Unidos por defecto
                country_us = env['res.country'].search([('code', '=', 'US')], limit=1)

                # Actualizar el nombre de la compañía por defecto
                company = env['res.company'].search([], limit=1)
                company.sudo().write({'name': company_name, 'country_id': country_us.id})

                # Crear el usuario interno
                user = env['res.users'].sudo().create({
                    'name': fullname,
                    'login': email,
                    'password': password,
                    'company_id': company.id,
                    'company_ids': [(6, 0, [company.id])],  # Asignar la compañía al usuario
                    'lang': lang,
                })

                # Asignar el grupo de usuario interno
                group_user = env.ref('base.group_user')
                user.groups_id = [(6, 0, [group_user.id])]  # Asignar al grupo "Usuario interno"

                # Asignar los grupos de seguridad correspondientes
                group_sales = env.ref('sales_team.group_sale_salesman_all_leads')  # Administrador de Ventas
                group_account_invoice = env.ref('account.group_account_invoice')  # Asesor Fiscal en Contabilidad
                group_account_manager = env.ref('account.group_account_manager')  # Validar Cuenta Bancaria en Banco
                group_stock_manager = env.ref('stock.group_stock_manager')  # Administrador de Inventario
                group_purchase_manager = env.ref('purchase.group_purchase_manager')  # Administrador de Compras
                group_erp_manager = env.ref('base.group_erp_manager')  # Administrador de Tablero
                group_partner_manager = env.ref('base.group_partner_manager')  # Creación de Contactos

                user.groups_id = [
                    (4, group_sales.id),
                    (4, group_account_invoice.id),
                    (4, group_account_manager.id),
                    (4, group_stock_manager.id),
                    (4, group_purchase_manager.id),
                    (4, group_erp_manager.id),
                    (4, group_partner_manager.id),
                ]

            # Redirigir al usuario a la página de inicio de sesión
            login_url = f"http://{http.request.httprequest.host}/web/login?db={db_name}"  # URL de inicio de sesión
            return http.request.redirect(login_url)

        except Exception as e:
            return http.request.render('easily_subscription.signup_form_template', {
                'error': f'Error al crear la compañía o el usuario: {str(e)}', **values, **errors
            })

    def _validate_email(self, email):
        """Validar el formato del correo electrónico."""
        regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return re.match(regex, email) is not None

    def _validate_fullname(self, fullname):
        """Validar que el nombre de usuario no exceda 50 caracteres."""
        return len(fullname) <= 50

    def _validate_password(self, password):
        """Validar que la contraseña sea fuerte."""
        if len(password) < 8:
            return False
        if not re.search(r'[A-Z]', password):  # Al menos una mayúscula
            return False
        if not re.search(r'[a-z]', password):  # Al menos una minúscula
            return False
        if not re.search(r'[0-9]', password):  # Al menos un número
            return False
        return True

    def _validate_recaptcha(self, recaptcha_response):
        """Validar el token de Google reCAPTCHA."""
        # @todo get secret_key from the odoo configuration
        secret_key = '6Lfun8wqAAAAAJsAWb-dtKykcnbuFRTSOZs6XwTn'  # Reemplaza con tu Secret Key
        payload = {
            'secret': secret_key,
            'response': recaptcha_response,
        }
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=payload)
        result = response.json()
        return result.get('success', False)
