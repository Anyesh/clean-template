from sqlalchemy.orm.exc import DetachedInstanceError


class ModelExtension:

    def update(self, db, data, commit=False, **kwargs):

        for attr, value in data.items():
            setattr(self, attr, value)

        db.session.flush()

        if commit:
            db.session.commit()

    def save(self, db, commit=True):
        db.session.add(self)
        db.session.flush()

        if commit:
            db.session.commit()

    def delete(self, db, commit=True):
        db.session.delete(self)
        db.session.flush()

        if commit:
            db.session.commit()

    def repr(self, **fields) -> str:
        """
        Helper for __repr__
        """

        field_strings = []
        at_least_one_attached_attribute = False

        for key, field in fields.items():

            try:
                field_strings.append(f'{key}={field!r}')
            except DetachedInstanceError:
                field_strings.append(f'{key}=DetachedInstanceError')
            else:
                at_least_one_attached_attribute = True

        if at_least_one_attached_attribute:
            return f"<{self.__class__.__name__}({','.join(field_strings)})>"

        return f"<{self.__class__.__name__}: ID#{id(self)}>"
