class ModelBase:
    __tablename__ = None
    __table_args__ = {}

    @classmethod
    @property
    def t_name(cls) -> str:
        """
        Returns schema.tablename as str
        """
        args = cls.__table_args__
        if isinstance(cls.__table_args__, tuple):
            args = cls.__table_args__[0]
        return f"{args.get('schema')}.{cls.__tablename__}"

